# Architecture Rules

> System boundaries and architectural constraints for the Notion Finance PPM Control Room

## System Boundaries

### Component Ownership

| Component | Directory | Language | Framework |
|-----------|-----------|----------|-----------|
| Control Room UI | `apps/control-room/` | TypeScript | Next.js 14+ |
| Notion Sync Service | `services/notion-sync/` | Python 3.11+ | httpx, pydantic |
| Databricks Jobs | `infra/databricks/` | Python/SQL | DAB, PySpark |
| Azure IaC | `infra/azure/` | Bicep | Azure RM |

### Layer Architecture

```
┌─────────────────────────────────────┐
│         Presentation Layer          │
│        (Control Room UI)            │
├─────────────────────────────────────┤
│            API Layer                │
│      (Next.js API Routes)           │
├─────────────────────────────────────┤
│          Data Layer                 │
│     (Databricks Lakehouse)          │
├─────────────────────────────────────┤
│        Ingestion Layer              │
│   (Notion Sync, Azure Ingest)       │
└─────────────────────────────────────┘
```

## Architectural Constraints

### 1. Medallion Architecture (Required)

All data must flow through bronze → silver → gold layers:

- **Bronze**: Raw, unprocessed data. Full payloads preserved.
- **Silver**: Cleaned, typed, normalized data.
- **Gold**: Aggregated, business-ready marts.

**Never skip layers.** Even simple transformations must go through all three.

### 2. Idempotency (Required)

All data operations must be idempotent:

```python
# Good: Upsert with deterministic key
df.write.format("delta").mode("overwrite") \
  .option("replaceWhere", f"page_id = '{page_id}'")

# Bad: Append without deduplication
df.write.format("delta").mode("append")
```

### 3. API Contract Stability

API endpoints must maintain backwards compatibility:

- Add new fields, never remove existing ones
- Use versioned endpoints for breaking changes (`/api/v2/...`)
- Document all changes in OpenAPI spec

### 4. Error Handling

All components must handle errors gracefully:

```typescript
// API responses
{
  "success": false,
  "error": {
    "code": "DATABRICKS_CONNECTION_ERROR",
    "message": "Failed to connect to Databricks",
    "details": {}
  }
}
```

### 5. Logging Standards

Use structured logging with correlation IDs:

```python
logger.info(
    "Synced database",
    extra={
        "correlation_id": correlation_id,
        "database_id": database_id,
        "pages_synced": count
    }
)
```

## Dependency Rules

### Allowed Dependencies (by layer)

| Layer | May Depend On |
|-------|---------------|
| UI | API only |
| API | Data Layer (Databricks) |
| Data Layer | Ingestion outputs (bronze tables) |
| Ingestion | External APIs (Notion, Azure) |

### Prohibited Dependencies

- UI must NOT query Databricks directly
- Ingestion must NOT write to gold tables
- API must NOT write to bronze tables

## File Organization

### Control Room App

```
apps/control-room/
├── src/
│   ├── app/          # Next.js App Router pages
│   ├── components/   # React components
│   │   └── ui/       # shadcn/ui primitives
│   └── lib/          # Utilities, clients
├── public/           # Static assets
└── package.json
```

### Notion Sync Service

```
services/notion-sync/
├── notion_sync/
│   ├── __init__.py
│   ├── sync.py       # Main sync logic
│   ├── client.py     # Notion API client
│   ├── models.py     # Pydantic models
│   └── config.py     # Configuration
├── tests/
└── pyproject.toml
```

### Databricks Bundle

```
infra/databricks/
├── databricks.yml    # DAB bundle definition
├── resources/        # Cluster, job configs
└── notebooks/        # Python/SQL notebooks
    ├── bronze/
    ├── silver/
    └── gold/
```

## Technology Choices

### Required

- Next.js 14+ with App Router
- TypeScript strict mode
- Python 3.11+ with type hints
- Delta Lake for all tables
- Databricks Asset Bundles for job deployment

### Preferred

- shadcn/ui for UI components
- Tailwind CSS for styling
- Zod for validation (TypeScript)
- Pydantic for validation (Python)
- httpx for HTTP clients (Python)

### Prohibited

- No jQuery or legacy libraries
- No REST clients without retry logic
- No SQL string concatenation (use parameterized queries)
- No hardcoded secrets (ever)
