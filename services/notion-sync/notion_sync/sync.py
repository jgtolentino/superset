"""Main sync logic for Notion to Databricks."""

import json
import time
from datetime import datetime, timezone
from typing import Optional

import structlog
from databricks import sql as databricks_sql
from databricks.sql.client import Connection

from notion_sync.client import NotionClient
from notion_sync.config import Config, DatabaseConfig
from notion_sync.models import BronzeRecord, NotionPage, SyncResult, SyncWatermark

logger = structlog.get_logger()


class DatabricksWriter:
    """Writes data to Databricks Delta tables."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self._connection: Optional[Connection] = None

    def connect(self) -> None:
        """Establish connection to Databricks SQL."""
        self._connection = databricks_sql.connect(
            server_hostname=self.config.databricks_host.replace("https://", ""),
            http_path=self.config.databricks_http_path,
            access_token=self.config.databricks_token,
        )
        logger.info("Connected to Databricks SQL")

    def close(self) -> None:
        """Close the Databricks connection."""
        if self._connection:
            self._connection.close()
            logger.info("Closed Databricks connection")

    def _get_cursor(self):
        """Get a database cursor."""
        if not self._connection:
            raise RuntimeError("Not connected to Databricks")
        return self._connection.cursor()

    def init_tables(self) -> None:
        """Create bronze tables if they don't exist."""
        catalog = self.config.databricks_catalog

        with self._get_cursor() as cursor:
            # Create bronze schema
            cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {catalog}.bronze")

            # Create raw pages table
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {catalog}.bronze.notion_raw_pages (
                    page_id STRING NOT NULL,
                    database_id STRING NOT NULL,
                    database_name STRING,
                    last_edited_time TIMESTAMP NOT NULL,
                    properties MAP<STRING, STRING>,
                    raw_payload STRING,
                    synced_at TIMESTAMP DEFAULT current_timestamp(),
                    _ingestion_timestamp TIMESTAMP DEFAULT current_timestamp()
                )
                USING DELTA
                PARTITIONED BY (database_name)
                TBLPROPERTIES (
                    'delta.autoOptimize.optimizeWrite' = 'true',
                    'delta.autoOptimize.autoCompact' = 'true'
                )
            """)

            # Create watermarks table
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {catalog}.bronze.sync_watermarks (
                    database_id STRING NOT NULL,
                    database_name STRING NOT NULL,
                    last_synced_time TIMESTAMP NOT NULL,
                    last_sync_run TIMESTAMP NOT NULL,
                    pages_synced BIGINT,
                    PRIMARY KEY (database_id)
                )
                USING DELTA
            """)

            logger.info("Initialized bronze tables")

    def get_watermark(self, database_id: str) -> Optional[SyncWatermark]:
        """Get the sync watermark for a database."""
        catalog = self.config.databricks_catalog

        with self._get_cursor() as cursor:
            cursor.execute(f"""
                SELECT database_id, database_name, last_synced_time,
                       last_sync_run, pages_synced
                FROM {catalog}.bronze.sync_watermarks
                WHERE database_id = ?
            """, (database_id,))

            row = cursor.fetchone()
            if row:
                return SyncWatermark(
                    database_id=row[0],
                    database_name=row[1],
                    last_synced_time=row[2],
                    last_sync_run=row[3],
                    pages_synced=row[4] or 0,
                )
            return None

    def update_watermark(self, watermark: SyncWatermark) -> None:
        """Update the sync watermark for a database."""
        catalog = self.config.databricks_catalog

        with self._get_cursor() as cursor:
            cursor.execute(f"""
                MERGE INTO {catalog}.bronze.sync_watermarks AS target
                USING (
                    SELECT ? AS database_id,
                           ? AS database_name,
                           ? AS last_synced_time,
                           ? AS last_sync_run,
                           ? AS pages_synced
                ) AS source
                ON target.database_id = source.database_id
                WHEN MATCHED THEN UPDATE SET
                    database_name = source.database_name,
                    last_synced_time = source.last_synced_time,
                    last_sync_run = source.last_sync_run,
                    pages_synced = source.pages_synced
                WHEN NOT MATCHED THEN INSERT (
                    database_id, database_name, last_synced_time,
                    last_sync_run, pages_synced
                ) VALUES (
                    source.database_id, source.database_name,
                    source.last_synced_time, source.last_sync_run,
                    source.pages_synced
                )
            """, (
                watermark.database_id,
                watermark.database_name,
                watermark.last_synced_time,
                watermark.last_sync_run,
                watermark.pages_synced,
            ))

        logger.debug(
            "Updated watermark",
            database_id=watermark.database_id,
            last_synced_time=watermark.last_synced_time.isoformat(),
        )

    def write_pages(
        self,
        pages: list[NotionPage],
        database_name: str,
    ) -> int:
        """Write pages to bronze table with upsert logic."""
        if not pages:
            return 0

        catalog = self.config.databricks_catalog
        synced_at = datetime.now(timezone.utc)

        # Prepare records
        records = []
        for page in pages:
            # Flatten properties for MAP column
            flat_props = {}
            for key, value in page.properties.items():
                flat_props[key] = json.dumps(value)

            records.append((
                page.page_id,
                page.database_id,
                database_name,
                page.last_edited_time,
                flat_props,
                json.dumps(page.raw_payload),
                synced_at,
            ))

        with self._get_cursor() as cursor:
            # Use MERGE for upsert
            for record in records:
                cursor.execute(f"""
                    MERGE INTO {catalog}.bronze.notion_raw_pages AS target
                    USING (
                        SELECT ? AS page_id,
                               ? AS database_id,
                               ? AS database_name,
                               ? AS last_edited_time,
                               ? AS properties,
                               ? AS raw_payload,
                               ? AS synced_at
                    ) AS source
                    ON target.page_id = source.page_id
                       AND target.database_id = source.database_id
                    WHEN MATCHED THEN UPDATE SET
                        last_edited_time = source.last_edited_time,
                        properties = source.properties,
                        raw_payload = source.raw_payload,
                        synced_at = source.synced_at
                    WHEN NOT MATCHED THEN INSERT (
                        page_id, database_id, database_name,
                        last_edited_time, properties, raw_payload, synced_at
                    ) VALUES (
                        source.page_id, source.database_id, source.database_name,
                        source.last_edited_time, source.properties,
                        source.raw_payload, source.synced_at
                    )
                """, record)

        logger.info(
            "Wrote pages to bronze",
            count=len(records),
            database_name=database_name,
        )

        return len(records)


class NotionSyncer:
    """Orchestrates sync from Notion to Databricks."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.writer = DatabricksWriter(config)

    async def sync_database(
        self,
        db_config: DatabaseConfig,
        full_refresh: bool = False,
    ) -> SyncResult:
        """Sync a single Notion database to bronze layer."""
        start_time = time.time()
        errors: list[str] = []
        pages_synced = 0
        pages_skipped = 0
        max_edited_time: Optional[datetime] = None

        log = logger.bind(
            database_id=db_config.id,
            database_name=db_config.name,
            full_refresh=full_refresh,
        )
        log.info("Starting database sync")

        try:
            # Get watermark for incremental sync
            since: Optional[datetime] = None
            if not full_refresh:
                watermark = self.writer.get_watermark(db_config.id)
                if watermark:
                    since = watermark.last_synced_time
                    log.info("Using watermark", since=since.isoformat())

            # Fetch pages from Notion
            pages_batch: list[NotionPage] = []
            batch_size = self.config.batch_size

            async with NotionClient(self.config) as client:
                async for page in client.iter_database_pages(db_config.id, since=since):
                    # Track max edited time for watermark
                    if max_edited_time is None or page.last_edited_time > max_edited_time:
                        max_edited_time = page.last_edited_time

                    # Skip archived pages for silver, but still store in bronze
                    pages_batch.append(page)

                    # Write in batches
                    if len(pages_batch) >= batch_size:
                        written = self.writer.write_pages(pages_batch, db_config.name)
                        pages_synced += written
                        pages_batch = []

                # Write remaining pages
                if pages_batch:
                    written = self.writer.write_pages(pages_batch, db_config.name)
                    pages_synced += written

            # Update watermark
            if max_edited_time:
                new_watermark = SyncWatermark(
                    database_id=db_config.id,
                    database_name=db_config.name,
                    last_synced_time=max_edited_time,
                    last_sync_run=datetime.now(timezone.utc),
                    pages_synced=pages_synced,
                )
                self.writer.update_watermark(new_watermark)

            log.info(
                "Completed database sync",
                pages_synced=pages_synced,
                pages_skipped=pages_skipped,
            )

        except Exception as e:
            log.error("Sync failed", error=str(e))
            errors.append(str(e))

        duration = time.time() - start_time

        return SyncResult(
            database_id=db_config.id,
            database_name=db_config.name,
            pages_synced=pages_synced,
            pages_skipped=pages_skipped,
            errors=errors,
            duration_seconds=duration,
            success=len(errors) == 0,
        )

    async def sync_all(self, full_refresh: bool = False) -> list[SyncResult]:
        """Sync all configured databases."""
        results: list[SyncResult] = []

        # Connect to Databricks
        self.writer.connect()

        try:
            # Initialize tables
            self.writer.init_tables()

            # Sync each database
            for db_config in self.config.get_databases():
                result = await self.sync_database(db_config, full_refresh)
                results.append(result)

        finally:
            self.writer.close()

        # Log summary
        total_pages = sum(r.pages_synced for r in results)
        failed = [r for r in results if not r.success]

        logger.info(
            "Sync complete",
            total_databases=len(results),
            total_pages=total_pages,
            failed_count=len(failed),
        )

        return results
