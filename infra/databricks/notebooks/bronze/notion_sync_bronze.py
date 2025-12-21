# Databricks notebook source
# MAGIC %md
# MAGIC # Notion Sync to Bronze Layer
# MAGIC
# MAGIC This notebook syncs Notion databases to the bronze layer.
# MAGIC It's typically invoked by the external notion-sync service,
# MAGIC but can also be run standalone for testing.

# COMMAND ----------

# MAGIC %md
# MAGIC ## Parameters

# COMMAND ----------

dbutils.widgets.text("catalog", "main", "Unity Catalog name")
catalog = dbutils.widgets.get("catalog")

print(f"Using catalog: {catalog}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Initialize Bronze Tables

# COMMAND ----------

# Create bronze schema if not exists
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.bronze")

# COMMAND ----------

# Create raw pages table
spark.sql(f"""
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

print("Created/verified bronze.notion_raw_pages table")

# COMMAND ----------

# Create watermarks table
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {catalog}.bronze.sync_watermarks (
    database_id STRING NOT NULL,
    database_name STRING NOT NULL,
    last_synced_time TIMESTAMP NOT NULL,
    last_sync_run TIMESTAMP NOT NULL,
    pages_synced BIGINT,
    PRIMARY KEY (database_id)
)
USING DELTA
TBLPROPERTIES (
    'delta.autoOptimize.optimizeWrite' = 'true'
)
""")

print("Created/verified bronze.sync_watermarks table")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Verify Table Status

# COMMAND ----------

# Show table stats
display(spark.sql(f"""
SELECT
    database_name,
    COUNT(*) as page_count,
    MAX(synced_at) as last_synced
FROM {catalog}.bronze.notion_raw_pages
GROUP BY database_name
"""))

# COMMAND ----------

# Show watermarks
display(spark.sql(f"""
SELECT * FROM {catalog}.bronze.sync_watermarks
ORDER BY last_sync_run DESC
"""))

# COMMAND ----------

# MAGIC %md
# MAGIC ## Manual Sync (Optional)
# MAGIC
# MAGIC Uncomment the code below to run a manual sync from this notebook.
# MAGIC Normally, sync is handled by the external notion-sync service.

# COMMAND ----------

# import os
# import sys
#
# # Install notion-sync package
# %pip install httpx pydantic pydantic-settings tenacity structlog
#
# # Add service to path (for local development)
# sys.path.insert(0, "/Workspace/Repos/your-repo/services/notion-sync")
#
# from notion_sync.config import Config
# from notion_sync.sync import NotionSyncer
#
# # Load config from secrets
# config = Config(
#     notion_api_key=dbutils.secrets.get("ppm-secrets", "notion-api-key"),
#     databricks_host=spark.conf.get("spark.databricks.workspaceUrl"),
#     databricks_token=dbutils.secrets.get("ppm-secrets", "databricks-token"),
#     databricks_http_path=dbutils.secrets.get("ppm-secrets", "databricks-http-path"),
#     databricks_catalog=catalog,
#     notion_programs_db_id=dbutils.secrets.get("ppm-secrets", "notion-programs-db-id"),
#     notion_projects_db_id=dbutils.secrets.get("ppm-secrets", "notion-projects-db-id"),
#     notion_budget_lines_db_id=dbutils.secrets.get("ppm-secrets", "notion-budget-lines-db-id"),
#     notion_risks_db_id=dbutils.secrets.get("ppm-secrets", "notion-risks-db-id"),
#     notion_actions_db_id=dbutils.secrets.get("ppm-secrets", "notion-actions-db-id"),
# )
#
# syncer = NotionSyncer(config)
# results = await syncer.sync_all()
#
# for result in results:
#     print(f"{result.database_name}: {result.pages_synced} pages synced")

# COMMAND ----------

print("Bronze layer initialization complete!")
