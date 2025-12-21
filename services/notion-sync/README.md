# Notion Sync Service

Sync Notion databases to Databricks bronze layer with incremental updates.

## Overview

This service:
- Pulls data from configured Notion databases
- Stores raw payloads in `bronze.notion_raw_pages`
- Tracks sync progress with watermarks for incremental sync
- Handles rate limiting and retries

## Quick Start

### 1. Install Dependencies

```bash
cd services/notion-sync
pip install -e ".[dev]"
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

Required environment variables:
- `NOTION_API_KEY` - Notion integration token
- `DATABRICKS_HOST` - Workspace URL
- `DATABRICKS_TOKEN` - Access token
- `DATABRICKS_HTTP_PATH` - SQL warehouse path
- `NOTION_*_DB_ID` - Database IDs to sync

### 3. Initialize Tables

```bash
notion-sync init-tables
```

### 4. Run Sync

```bash
# Incremental sync (using watermarks)
notion-sync sync

# Full refresh
notion-sync sync --full-refresh

# Sync specific database
notion-sync sync -d projects
```

## CLI Commands

```bash
# Check health of connections
notion-sync health

# List configured databases
notion-sync list-databases

# Initialize bronze tables
notion-sync init-tables

# Run sync
notion-sync sync [--full-refresh] [-d DATABASE]
```

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐
│   Notion    │────▶│ Notion Sync │────▶│     Databricks      │
│    API      │     │   Service   │     │   bronze.notion_*   │
└─────────────┘     └─────────────┘     └─────────────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │ Watermarks  │
                    │   Table     │
                    └─────────────┘
```

## Database Mapping

| Notion Database | Target Table |
|-----------------|--------------|
| Programs | `bronze.notion_raw_pages` (database_name='programs') |
| Projects | `bronze.notion_raw_pages` (database_name='projects') |
| Budget Lines | `bronze.notion_raw_pages` (database_name='budget_lines') |
| Risks | `bronze.notion_raw_pages` (database_name='risks') |
| Actions | `bronze.notion_raw_pages` (database_name='actions') |

## Sync Behavior

### Incremental Sync

1. Read watermark for database (`last_edited_time`)
2. Query Notion for pages edited after watermark
3. Upsert pages to bronze table
4. Update watermark with latest `last_edited_time`

### Full Refresh

1. Query all pages from Notion database
2. Upsert all pages to bronze table
3. Update watermark

### Upsert Logic

Pages are upserted by `(page_id, database_id)` composite key:
- Existing pages are updated
- New pages are inserted
- Archived pages are still stored (for audit)

## Error Handling

### Rate Limiting

- Notion API: 3 requests/second
- Service enforces 340ms delay between requests
- 429 responses trigger exponential backoff

### Retries

- Max 3 retries with exponential backoff
- Backoff: 1s, 2s, 4s
- Transient errors (5xx, rate limits) are retried

### Connection Errors

- Databricks connection verified at startup
- Connection errors fail the sync
- Partial syncs are safe (idempotent)

## Development

### Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=notion_sync --cov-report=html

# Specific test file
pytest tests/test_client.py -v
```

### Code Quality

```bash
# Format code
black notion_sync tests
isort notion_sync tests

# Type checking
mypy notion_sync

# Linting
ruff check notion_sync tests
```

### Local Development

```bash
# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run with local .env
notion-sync --env-file .env.local sync
```

## Troubleshooting

### "BLOCKED: missing env var"

Set the required environment variable:
```bash
export NOTION_API_KEY="your-key"
```

### "BLOCKED: suspicious default value"

Replace placeholder values with actual credentials.

### Rate limit errors

Increase `RATE_LIMIT_DELAY` or reduce `BATCH_SIZE`.

### Connection refused

Check `DATABRICKS_HOST` and `DATABRICKS_HTTP_PATH` values.

## Security

- Never commit `.env` files
- Use service principal tokens for production
- Rotate tokens regularly
- Store secrets in Azure Key Vault for production
