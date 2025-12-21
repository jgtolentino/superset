"""CLI entry point for Notion Sync service."""

import asyncio
import sys
from pathlib import Path

import click
import structlog
from dotenv import load_dotenv

from notion_sync.config import Config
from notion_sync.sync import NotionSyncer

# Configure structlog
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
        if sys.stdout.isatty()
        else structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


def validate_environment() -> bool:
    """Validate required environment variables are set."""
    required = [
        "NOTION_API_KEY",
        "DATABRICKS_HOST",
        "DATABRICKS_TOKEN",
    ]

    missing = []
    for var in required:
        import os
        value = os.environ.get(var, "")
        if not value:
            missing.append(var)
        elif value.lower() in ["changeme", "password", "secret"]:
            logger.error(f"BLOCKED: suspicious default value in {var}")
            return False

    if missing:
        for var in missing:
            logger.error(f"BLOCKED: missing env var {var}")
        return False

    return True


@click.group()
@click.option("--env-file", type=click.Path(exists=True), help="Path to .env file")
def cli(env_file: str | None) -> None:
    """Notion Sync CLI - Sync Notion databases to Databricks."""
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()


@cli.command()
@click.option("--full-refresh", is_flag=True, help="Ignore watermarks and sync all")
@click.option("--database", "-d", multiple=True, help="Sync specific database(s) only")
def sync(full_refresh: bool, database: tuple[str, ...]) -> None:
    """Run sync for all configured databases."""
    if not validate_environment():
        sys.exit(1)

    try:
        config = Config()  # type: ignore[call-arg]
    except Exception as e:
        logger.error("Configuration error", error=str(e))
        sys.exit(1)

    syncer = NotionSyncer(config)

    # Run async sync
    async def run_sync():
        if database:
            # Filter to specific databases
            results = []
            for db_config in config.get_databases():
                if db_config.name in database or db_config.id in database:
                    result = await syncer.sync_database(db_config, full_refresh)
                    results.append(result)
            return results
        else:
            return await syncer.sync_all(full_refresh)

    results = asyncio.run(run_sync())

    # Report results
    success_count = sum(1 for r in results if r.success)
    total_pages = sum(r.pages_synced for r in results)

    click.echo(f"\nSync Complete:")
    click.echo(f"  Databases: {success_count}/{len(results)} successful")
    click.echo(f"  Pages synced: {total_pages}")

    for result in results:
        status = "OK" if result.success else "FAILED"
        click.echo(f"  - {result.database_name}: {status} ({result.pages_synced} pages)")
        if result.errors:
            for error in result.errors:
                click.echo(f"      Error: {error}")

    # Exit with error if any failed
    if success_count < len(results):
        sys.exit(1)


@cli.command()
def health() -> None:
    """Check health of Notion and Databricks connections."""
    if not validate_environment():
        sys.exit(1)

    try:
        config = Config()  # type: ignore[call-arg]
    except Exception as e:
        click.echo(f"Configuration error: {e}", err=True)
        sys.exit(1)

    async def check_health():
        from notion_sync.client import NotionClient
        from notion_sync.sync import DatabricksWriter

        # Check Notion
        click.echo("Checking Notion API...")
        async with NotionClient(config) as client:
            notion_ok = await client.health_check()
        click.echo(f"  Notion: {'OK' if notion_ok else 'FAILED'}")

        # Check Databricks
        click.echo("Checking Databricks...")
        writer = DatabricksWriter(config)
        try:
            writer.connect()
            databricks_ok = True
            writer.close()
        except Exception as e:
            databricks_ok = False
            click.echo(f"  Error: {e}", err=True)

        click.echo(f"  Databricks: {'OK' if databricks_ok else 'FAILED'}")

        return notion_ok and databricks_ok

    healthy = asyncio.run(check_health())

    if healthy:
        click.echo("\nAll systems healthy!")
    else:
        click.echo("\nHealth check failed!", err=True)
        sys.exit(1)


@cli.command()
def list_databases() -> None:
    """List configured databases."""
    if not validate_environment():
        sys.exit(1)

    try:
        config = Config()  # type: ignore[call-arg]
    except Exception as e:
        click.echo(f"Configuration error: {e}", err=True)
        sys.exit(1)

    databases = config.get_databases()

    click.echo("Configured databases:")
    for db in databases:
        click.echo(f"  - {db.name}: {db.id[:8]}...")
        click.echo(f"    Sync interval: {db.sync_interval}s")
        click.echo(f"    Fields: {len(db.field_mappings)}")

    if not databases:
        click.echo("  No databases configured. Set NOTION_*_DB_ID env vars.")


@cli.command()
def init_tables() -> None:
    """Initialize Databricks bronze tables."""
    if not validate_environment():
        sys.exit(1)

    try:
        config = Config()  # type: ignore[call-arg]
    except Exception as e:
        click.echo(f"Configuration error: {e}", err=True)
        sys.exit(1)

    from notion_sync.sync import DatabricksWriter

    writer = DatabricksWriter(config)
    writer.connect()

    try:
        writer.init_tables()
        click.echo("Bronze tables initialized successfully!")
    finally:
        writer.close()


if __name__ == "__main__":
    cli()
