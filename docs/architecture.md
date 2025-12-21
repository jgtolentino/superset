# Notion x Finance PPM - Architecture Documentation

## Overview

The Notion Finance PPM (Project Portfolio Management) system provides a unified platform for managing financial portfolios, tracking project health, monitoring data pipelines, and surfacing Azure Advisor recommendations. The architecture follows a medallion data lakehouse pattern with a modern web UI.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATA SOURCES                                    │
├─────────────────┬─────────────────────────┬─────────────────────────────────┤
│   Notion API    │   Azure Resource Graph   │        Azure Advisor           │
│   (Databases)   │     (Resources)          │      (Recommendations)         │
└────────┬────────┴───────────┬──────────────┴───────────────┬────────────────┘
         │                    │                              │
         ▼                    ▼                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         INGESTION LAYER                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│  notion-sync (Python)      │  Azure RG Ingest Notebook                      │
│  - Async HTTP client       │  - Service Principal auth                      │
│  - Watermark-based sync    │  - Paginated KQL queries                       │
│  - Rate limiting           │  - Delta Lake writes                           │
└─────────────────────────────────────────────────────────────────────────────┘
         │                              │
         ▼                              ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BRONZE LAYER (Raw)                                   │
│                         main.bronze.*                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  notion_raw_pages          │  azure_resources          │  azure_advisor     │
│  notion_sync_watermarks    │                           │                    │
└─────────────────────────────────────────────────────────────────────────────┘
         │                              │                           │
         ▼                              ▼                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SILVER LAYER (Curated)                               │
│                         main.silver.*                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│  programs    │  projects   │  budget_lines  │  risks  │  actions  │ advisor │
└─────────────────────────────────────────────────────────────────────────────┘
         │                              │                           │
         ▼                              ▼                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GOLD LAYER (Analytics)                               │
│                         main.gold.*                                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  budget_vs_actual  │  project_health  │  forecast  │  control_room_status  │
│  advisor_summary   │  data_quality_issues                                   │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                      Control Room (Next.js)                                  │
│  ┌─────────────┬─────────────┬─────────────┬──────────────┬─────────────┐   │
│  │  /overview  │ /pipelines  │ /data-quality│  /advisor   │  /projects  │   │
│  └─────────────┴─────────────┴─────────────┴──────────────┴─────────────┘   │
│                              │                                               │
│                              ▼                                               │
│                    Databricks SQL Connector                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### 1. Data Sources

#### Notion API
- **Purpose**: Source of truth for Programs, Projects, Budget Lines, Risks, and Actions
- **API Version**: 2022-06-28
- **Authentication**: Integration token (Bearer auth)
- **Sync Strategy**: Incremental using `last_edited_time` watermarks

#### Azure Resource Graph
- **Purpose**: Cloud resource inventory and metadata
- **Authentication**: Service Principal (Client Credentials)
- **Query Language**: Kusto Query Language (KQL)
- **Sync Strategy**: Full refresh with MERGE upsert

#### Azure Advisor
- **Purpose**: Cost, security, reliability, and performance recommendations
- **Authentication**: Service Principal (Client Credentials)
- **Categories**: Cost, HighAvailability, Security, Performance, OperationalExcellence
- **Sync Strategy**: Full refresh with MERGE upsert

### 2. Ingestion Layer

#### notion-sync Service
- **Language**: Python 3.11+
- **Framework**: httpx (async HTTP), pydantic (validation)
- **Features**:
  - Async/await for high throughput
  - Exponential backoff retry (3 attempts)
  - Rate limiting compliance (3 req/sec default)
  - Watermark-based incremental sync
  - Databricks SDK for Delta Lake writes

#### Azure Ingest Notebooks
- **Runtime**: Databricks Runtime 13.3 LTS
- **Features**:
  - Service Principal authentication
  - Paginated API calls
  - Delta Lake MERGE operations
  - Error handling with logging

### 3. Data Lakehouse (Databricks)

#### Bronze Layer
Raw data ingested from sources with minimal transformation:
- `notion_raw_pages`: Complete Notion page JSON
- `notion_sync_watermarks`: Sync state tracking
- `azure_resources`: Raw Azure resource data
- `azure_advisor`: Raw advisor recommendations

#### Silver Layer
Cleaned, validated, and typed data:
- `programs`: Financial programs with budgets
- `projects`: Individual projects with status
- `budget_lines`: Line-item budget tracking
- `risks`: Risk register entries
- `actions`: Action items and tasks
- `advisor_recommendations`: Typed advisor data

#### Gold Layer
Business-ready aggregations and KPIs:
- `budget_vs_actual`: Budget variance analysis
- `project_health`: Health scores and trends
- `forecast`: Financial forecasting
- `control_room_status`: Pipeline and system status
- `advisor_summary`: Aggregated recommendations
- `data_quality_issues`: DQ check results

### 4. Control Room UI

#### Technology Stack
- **Framework**: Next.js 14 (App Router)
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **Validation**: Zod
- **Data Fetching**: Server Components + API Routes

#### Pages
| Route | Purpose |
|-------|---------|
| `/overview` | KPI dashboard, health summary, alerts |
| `/pipelines` | Job status, run history, errors |
| `/data-quality` | DQ issues by category and severity |
| `/advisor` | Azure recommendations by category |
| `/projects` | Project portfolio explorer |

#### API Routes
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Application health check |
| `/api/kpis` | GET | Dashboard KPIs |
| `/api/jobs` | GET | Pipeline job status |
| `/api/dq/issues` | GET | Data quality issues |
| `/api/advisor/recommendations` | GET | Advisor recommendations |
| `/api/notion/actions` | GET/POST | Action queue management |

### 5. CI/CD Pipeline

```
┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│   Pull Request    │────▶│      CI Run       │────▶│   Code Review     │
└───────────────────┘     └───────────────────┘     └───────────────────┘
                                   │
                                   ▼
┌───────────────────────────────────────────────────────────────────────┐
│                           CI Checks                                    │
├───────────────────┬───────────────────┬───────────────────────────────┤
│  Python Lint/Test │  TypeScript Build │  DAB Validation               │
│  (ruff, pytest)   │  (tsc, npm build) │  (databricks validate)        │
└───────────────────┴───────────────────┴───────────────────────────────┘
                                   │
                                   ▼
┌───────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│   Merge to main   │────▶│  Deploy Staging   │────▶│  Deploy Prod      │
└───────────────────┘     └───────────────────┘     └───────────────────┘
```

## Security Architecture

### Authentication & Authorization
- **Notion**: Integration token with database-level permissions
- **Databricks**: Personal Access Token or Service Principal
- **Azure**: Service Principal with Resource Graph Reader role
- **Control Room**: Environment-based configuration (no embedded secrets)

### Secret Management
- Development: `.env` files (gitignored)
- CI/CD: GitHub Actions secrets
- Production: Platform secret stores (DigitalOcean, Kubernetes)

### Data Security
- All API calls over HTTPS
- Credentials never logged or committed
- Sensitive columns masked in logs
- Audit logging for all data access

## Deployment Architecture

### Development
```bash
./scripts/dev_up.sh  # Local setup with mock data
```

### Staging
- Triggered on PR merge to main
- Automatic deployment via GitHub Actions
- Databricks bundle deployed to dev/staging targets

### Production
- Manual approval required
- Databricks bundle deployed to prod target
- Control Room deployed to production environment

## Scalability Considerations

### Data Volume
- Notion: Supports millions of pages via incremental sync
- Azure: Paginated API calls handle large resource counts
- Databricks: Auto-scaling clusters for processing

### Performance
- Control Room: Server-side rendering + caching
- API Routes: Connection pooling to Databricks
- Notebooks: Spark parallel processing

## Disaster Recovery

### Data Backups
- Delta Lake: Time travel (30-day retention)
- Databricks: Unity Catalog managed backups
- Notion: Source system responsibility

### Recovery Procedures
1. **Pipeline Failure**: Re-run job from Databricks UI
2. **Data Corruption**: Delta Lake time travel restore
3. **Sync Gap**: Full refresh with `--full-refresh` flag

## Monitoring & Observability

### Metrics
- Pipeline job success/failure rates
- Data freshness (last sync timestamps)
- Row counts and data quality scores
- API response times

### Alerting
- Job failure notifications
- Data quality threshold breaches
- Stale data warnings (>24h without sync)

### Logging
- Structured JSON logging
- Correlation IDs across services
- Error stack traces with context
