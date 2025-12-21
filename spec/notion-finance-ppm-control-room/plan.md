# Notion Finance PPM Control Room - Implementation Plan

> Technical architecture and implementation roadmap

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Platform Architecture                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                         Data Sources Layer                                │  │
│  ├──────────────────┬──────────────────┬──────────────────────────────────┤  │
│  │      Notion      │   Azure Advisor  │   Azure Resource Graph           │  │
│  │   (PPM Data)     │  (Recommendations)│   (Resource Inventory)          │  │
│  └────────┬─────────┴────────┬─────────┴──────────────┬───────────────────┘  │
│           │                   │                        │                       │
│           ▼                   ▼                        ▼                       │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                         Ingestion Layer                                   │  │
│  ├──────────────────┬──────────────────┬──────────────────────────────────┤  │
│  │   Notion Sync    │  Advisor Ingest  │   Resource Graph Ingest          │  │
│  │    Service       │     Job          │         Job                      │  │
│  │   (Python)       │  (Databricks)    │     (Databricks)                 │  │
│  └────────┬─────────┴────────┬─────────┴──────────────┬───────────────────┘  │
│           │                   │                        │                       │
│           ▼                   ▼                        ▼                       │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                     Databricks Lakehouse                                  │  │
│  ├──────────────────────────────────────────────────────────────────────────┤  │
│  │  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────────────┐  │  │
│  │  │   Bronze    │───▶│   Silver    │───▶│           Gold              │  │  │
│  │  │  (Raw)      │    │(Normalized) │    │  (KPIs, Marts, Metrics)     │  │  │
│  │  └─────────────┘    └─────────────┘    └─────────────────────────────┘  │  │
│  │                                                                          │  │
│  │  Tables:                                                                 │  │
│  │  - bronze.notion_raw_pages              - gold.ppm_budget_vs_actual     │  │
│  │  - bronze.azure_rg_raw                  - gold.ppm_forecast             │  │
│  │  - silver.notion_programs               - gold.ppm_project_health       │  │
│  │  - silver.notion_projects               - gold.azure_advisor_recs       │  │
│  │  - silver.notion_budget_lines           - gold.control_room_status      │  │
│  │  - silver.notion_risks                  - gold.data_quality_metrics     │  │
│  │  - silver.notion_actions                                                │  │
│  │  - silver.azure_advisor_recommendations                                 │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                         │                                       │
│                                         ▼                                       │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                           API Layer                                       │  │
│  ├──────────────────────────────────────────────────────────────────────────┤  │
│  │  Next.js API Routes (or FastAPI)                                         │  │
│  │  - /api/health                    - /api/dq/issues                       │  │
│  │  - /api/kpis                      - /api/advisor/recommendations         │  │
│  │  - /api/jobs                      - /api/notion/actions                  │  │
│  │  - /api/job-runs                                                         │  │
│  └────────────────────────────────────────────────────────────────────────┬─┘  │
│                                                                            │    │
│                                         ▼                                  │    │
│  ┌──────────────────────────────────────────────────────────────────────────┐  │
│  │                       Control Room UI                                     │  │
│  ├──────────────────────────────────────────────────────────────────────────┤  │
│  │  Next.js + Tailwind CSS                                                  │  │
│  │  Pages: /overview  /pipelines  /data-quality  /advisor  /projects        │  │
│  └──────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Design

### 1. Notion Sync Service

**Purpose**: Pull data from Notion API and write to Databricks bronze layer.

**Implementation**:
```python
# services/notion-sync/notion_sync/sync.py

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import httpx
from pydantic import BaseModel

class NotionPage(BaseModel):
    """Normalized Notion page representation."""
    page_id: str
    database_id: str
    last_edited_time: datetime
    properties: dict
    raw_payload: dict

class NotionSyncer:
    """Incremental syncer for Notion databases."""

    def __init__(self, api_key: str, databricks_client):
        self.api_key = api_key
        self.databricks = databricks_client
        self.base_url = "https://api.notion.com/v1"

    async def sync_database(self, database_id: str) -> int:
        """Sync a single Notion database to bronze."""
        watermark = await self._get_watermark(database_id)
        pages = await self._fetch_pages(database_id, since=watermark)

        if not pages:
            return 0

        await self._write_to_bronze(pages)
        await self._update_watermark(database_id, max(p.last_edited_time for p in pages))

        return len(pages)

    async def _fetch_pages(self, database_id: str, since: Optional[datetime] = None):
        """Fetch pages from Notion with optional time filter."""
        # Implementation with pagination and rate limiting
        pass

    async def _write_to_bronze(self, pages: list[NotionPage]):
        """Write pages to bronze.notion_raw_pages."""
        # Implementation using Databricks SQL or Delta
        pass
```

**Configuration**:
```yaml
# services/notion-sync/config.yaml
databases:
  - id: ${NOTION_PROGRAMS_DB_ID}
    name: programs
    sync_interval: 300  # 5 minutes
  - id: ${NOTION_PROJECTS_DB_ID}
    name: projects
    sync_interval: 300
  - id: ${NOTION_BUDGET_LINES_DB_ID}
    name: budget_lines
    sync_interval: 300
  - id: ${NOTION_RISKS_DB_ID}
    name: risks
    sync_interval: 300
  - id: ${NOTION_ACTIONS_DB_ID}
    name: actions
    sync_interval: 300

settings:
  batch_size: 100
  max_retries: 3
  backoff_factor: 2
```

### 2. Databricks Jobs (DAB Bundle)

**Purpose**: Transform data through medallion layers and compute KPIs.

**Job Definitions**:
```yaml
# infra/databricks/databricks.yml
bundle:
  name: notion-finance-ppm

workspace:
  host: ${DATABRICKS_HOST}

resources:
  jobs:
    notion_sync_bronze:
      name: "[PPM] Notion Sync Bronze"
      schedule:
        quartz_cron_expression: "0 */5 * * * ?"
        timezone_id: UTC
      tasks:
        - task_key: sync
          notebook_task:
            notebook_path: ./notebooks/notion_sync_bronze.py
          clusters:
            - job_cluster_key: small
      job_clusters:
        - job_cluster_key: small
          new_cluster:
            spark_version: 14.3.x-scala2.12
            node_type_id: Standard_DS3_v2
            num_workers: 0
            spark_conf:
              spark.master: "local[*]"

    notion_transform_silver:
      name: "[PPM] Transform Silver"
      schedule:
        quartz_cron_expression: "0 */10 * * * ?"
        timezone_id: UTC
      tasks:
        - task_key: transform
          depends_on: []
          notebook_task:
            notebook_path: ./notebooks/notion_transform_silver.py

    ppm_marts_gold:
      name: "[PPM] Compute Gold Marts"
      schedule:
        quartz_cron_expression: "0 0 * * * ?"
        timezone_id: UTC
      tasks:
        - task_key: budget_vs_actual
          notebook_task:
            notebook_path: ./notebooks/gold_budget_vs_actual.py
        - task_key: project_health
          notebook_task:
            notebook_path: ./notebooks/gold_project_health.py
        - task_key: forecast
          depends_on:
            - task_key: budget_vs_actual
          notebook_task:
            notebook_path: ./notebooks/gold_forecast.py

    azure_rg_ingest_bronze:
      name: "[PPM] Azure Resource Graph Ingest"
      schedule:
        quartz_cron_expression: "0 0 6 * * ?"
        timezone_id: UTC
      tasks:
        - task_key: ingest
          notebook_task:
            notebook_path: ./notebooks/azure_rg_ingest.py

    azure_advisor_transform:
      name: "[PPM] Azure Advisor Transform"
      schedule:
        quartz_cron_expression: "0 30 6 * * ?"
        timezone_id: UTC
      tasks:
        - task_key: transform
          depends_on: []
          notebook_task:
            notebook_path: ./notebooks/azure_advisor_transform.py

    control_room_status_refresh:
      name: "[PPM] Control Room Status"
      schedule:
        quartz_cron_expression: "0 */15 * * * ?"
        timezone_id: UTC
      tasks:
        - task_key: refresh
          notebook_task:
            notebook_path: ./notebooks/control_room_status.py
```

### 3. Control Room API

**Purpose**: Serve data to Control Room UI and external consumers.

**Implementation** (Next.js API routes):
```typescript
// apps/control-room/src/app/api/kpis/route.ts

import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { DatabricksClient } from '@/lib/databricks';

const KPIQuerySchema = z.object({
  from: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  to: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  dimensions: z.array(z.string()).optional(),
});

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);

  const query = KPIQuerySchema.parse({
    from: searchParams.get('from'),
    to: searchParams.get('to'),
    dimensions: searchParams.getAll('dimension'),
  });

  const client = new DatabricksClient();
  const kpis = await client.query(`
    SELECT
      metric_name,
      dimension,
      dimension_value,
      period,
      value,
      unit
    FROM gold.ppm_budget_vs_actual
    WHERE period BETWEEN '${query.from}' AND '${query.to}'
    ORDER BY period, metric_name
  `);

  return NextResponse.json({ data: kpis });
}
```

### 4. Control Room UI

**Purpose**: Visual interface for KPIs, health, and actions.

**Component Structure**:
```
apps/control-room/src/
├── app/
│   ├── layout.tsx              # Root layout with nav
│   ├── page.tsx                # Redirect to /overview
│   ├── overview/
│   │   └── page.tsx            # Dashboard home
│   ├── pipelines/
│   │   └── page.tsx            # Pipeline monitoring
│   ├── data-quality/
│   │   └── page.tsx            # DQ dashboard
│   ├── advisor/
│   │   └── page.tsx            # Azure Advisor view
│   └── projects/
│       └── page.tsx            # Project explorer
├── components/
│   ├── ui/                     # Shadcn/ui components
│   ├── kpi-card.tsx
│   ├── job-status-table.tsx
│   ├── dq-issue-list.tsx
│   ├── advisor-summary.tsx
│   └── project-table.tsx
└── lib/
    ├── databricks.ts           # Databricks client
    ├── notion.ts               # Notion client for actions
    └── utils.ts                # Helpers
```

**Key Components**:
```tsx
// apps/control-room/src/components/kpi-card.tsx

interface KPICardProps {
  title: string;
  value: number;
  unit: string;
  trend?: 'up' | 'down' | 'stable';
  trendValue?: number;
  status?: 'success' | 'warning' | 'error';
}

export function KPICard({ title, value, unit, trend, trendValue, status }: KPICardProps) {
  return (
    <div className={`rounded-lg border p-4 ${statusColors[status || 'success']}`}>
      <h3 className="text-sm font-medium text-muted-foreground">{title}</h3>
      <div className="mt-2 flex items-baseline gap-2">
        <span className="text-2xl font-bold">{value.toLocaleString()}</span>
        <span className="text-sm text-muted-foreground">{unit}</span>
      </div>
      {trend && (
        <div className="mt-2 flex items-center gap-1 text-sm">
          <TrendIcon direction={trend} />
          <span>{trendValue}% vs last period</span>
        </div>
      )}
    </div>
  );
}
```

---

## Implementation Milestones

### M1: Foundation (Phase 1)

**Deliverables**:
- Repository structure
- Spec Kit bundle
- Basic CI/CD
- Continue rules

**Tasks**:
1. Create monorepo structure
2. Write spec documents
3. Set up GitHub Actions
4. Create Continue guardrails
5. Set up development environment

**Exit Criteria**:
- [ ] All directories created
- [ ] CI passes
- [ ] Continue rules enforced
- [ ] Dev environment documented

### M2: Notion Sync Service (Phase 2)

**Deliverables**:
- Python sync service
- Notion API integration
- Bronze layer tables
- Watermark tracking

**Tasks**:
1. Implement NotionSyncer class
2. Create database configuration
3. Write bronze table DDL
4. Implement watermark logic
5. Unit tests (80% coverage)
6. Integration tests

**Exit Criteria**:
- [ ] Syncs all 5 databases
- [ ] Incremental by watermark
- [ ] Idempotent writes
- [ ] < 10 min sync lag

### M3: Databricks Bundle (Phase 3)

**Deliverables**:
- DAB configuration
- Bronze → Silver notebooks
- Silver → Gold notebooks
- Job run metadata tables

**Tasks**:
1. Define DAB bundle
2. Write transformation notebooks
3. Create gold mart queries
4. Set up job schedules
5. Implement run metadata capture
6. Deploy to workspace

**Exit Criteria**:
- [ ] All jobs deploy successfully
- [ ] Transformations pass validation
- [ ] Gold marts populated
- [ ] Job runs tracked

### M4: Azure Integration (Phase 4)

**Deliverables**:
- Resource Graph ingestion
- Advisor recommendations
- Cost/security signals
- Linked to projects

**Tasks**:
1. Azure authentication setup
2. Resource Graph query notebooks
3. Advisor normalization
4. Gold layer aggregation
5. Project linking logic

**Exit Criteria**:
- [ ] Daily Advisor sync
- [ ] Recommendations in gold
- [ ] Cost savings calculated
- [ ] Links to projects work

### M5: Control Room API (Phase 5)

**Deliverables**:
- Next.js API routes
- Databricks connection
- All endpoints functional
- OpenAPI documentation

**Tasks**:
1. Set up Next.js project
2. Implement Databricks client
3. Build all API routes
4. Add authentication
5. Write API tests
6. Generate OpenAPI spec

**Exit Criteria**:
- [ ] All endpoints return data
- [ ] < 500ms p99 response
- [ ] Auth working
- [ ] Docs complete

### M6: Control Room UI (Phase 6)

**Deliverables**:
- All 5 pages
- Responsive design
- Data visualizations
- Push-to-Notion action

**Tasks**:
1. Build page layouts
2. Implement KPI cards
3. Create data tables
4. Add charts (Recharts)
5. Implement Notion action
6. Mobile responsiveness

**Exit Criteria**:
- [ ] All pages functional
- [ ] Data displays correctly
- [ ] Actions work
- [ ] Mobile-friendly

### M7: CI/CD & Deployment (Phase 7)

**Deliverables**:
- Full CI pipeline
- Deployment workflows
- Infrastructure as code
- Monitoring setup

**Tasks**:
1. CI workflow (lint, test, build)
2. Deploy Control Room workflow
3. Deploy Databricks workflow
4. Infrastructure definitions
5. Health check scripts
6. Alerting configuration

**Exit Criteria**:
- [ ] CI passes on all PRs
- [ ] Deployments automated
- [ ] Health checks pass
- [ ] Alerts configured

### M8: Documentation & Verification (Phase 8)

**Deliverables**:
- Architecture docs
- Runbooks
- Data dictionary
- Verification scripts

**Tasks**:
1. Write architecture.md
2. Write runbooks.md
3. Write data-dictionary.md
4. Create dev_up.sh
5. Create health_check.sh
6. Create dab_deploy.sh

**Exit Criteria**:
- [ ] All docs complete
- [ ] Scripts tested
- [ ] End-to-end verified
- [ ] Ready for production

---

## Technical Specifications

### Database Schema (Databricks)

**Bronze Layer**:
```sql
CREATE TABLE IF NOT EXISTS bronze.notion_raw_pages (
  page_id STRING NOT NULL,
  database_id STRING NOT NULL,
  database_name STRING,
  last_edited_time TIMESTAMP NOT NULL,
  properties MAP<STRING, STRING>,
  raw_payload STRING,  -- JSON
  synced_at TIMESTAMP DEFAULT current_timestamp(),
  _ingestion_timestamp TIMESTAMP DEFAULT current_timestamp()
)
USING DELTA
PARTITIONED BY (database_name)
TBLPROPERTIES (
  delta.autoOptimize.optimizeWrite = true,
  delta.autoOptimize.autoCompact = true
);

CREATE TABLE IF NOT EXISTS bronze.azure_rg_raw (
  resource_id STRING NOT NULL,
  resource_type STRING,
  resource_group STRING,
  subscription_id STRING,
  properties STRING,  -- JSON
  advisor_recommendations STRING,  -- JSON
  ingested_at TIMESTAMP DEFAULT current_timestamp()
)
USING DELTA;
```

**Silver Layer**:
```sql
CREATE TABLE IF NOT EXISTS silver.notion_projects (
  project_id STRING NOT NULL,
  program_id STRING,
  name STRING NOT NULL,
  budget_total DECIMAL(18, 2),
  currency STRING DEFAULT 'USD',
  start_date DATE,
  end_date DATE,
  status STRING,
  priority STRING,
  owner STRING,
  is_archived BOOLEAN DEFAULT false,
  last_modified TIMESTAMP,
  synced_at TIMESTAMP,
  PRIMARY KEY (project_id)
)
USING DELTA;

CREATE TABLE IF NOT EXISTS silver.notion_budget_lines (
  budget_line_id STRING NOT NULL,
  project_id STRING NOT NULL,
  category STRING,  -- CapEx, OpEx
  vendor STRING,
  amount DECIMAL(18, 2),
  committed_date DATE,
  invoice_date DATE,
  paid_date DATE,
  actual_amount DECIMAL(18, 2),
  notes STRING,
  is_archived BOOLEAN DEFAULT false,
  last_modified TIMESTAMP,
  synced_at TIMESTAMP,
  PRIMARY KEY (budget_line_id)
)
USING DELTA;
```

**Gold Layer**:
```sql
CREATE TABLE IF NOT EXISTS gold.ppm_budget_vs_actual (
  metric_id STRING NOT NULL,
  metric_name STRING NOT NULL,  -- budget, actual, variance
  dimension STRING NOT NULL,    -- program, project, category
  dimension_value STRING NOT NULL,
  period DATE NOT NULL,
  value DECIMAL(18, 2),
  unit STRING DEFAULT 'USD',
  computed_at TIMESTAMP DEFAULT current_timestamp(),
  PRIMARY KEY (metric_id)
)
USING DELTA
PARTITIONED BY (period);

CREATE TABLE IF NOT EXISTS gold.control_room_status (
  job_id STRING NOT NULL,
  job_name STRING NOT NULL,
  last_run_id STRING,
  last_run_status STRING,
  last_run_time TIMESTAMP,
  last_run_duration_seconds INT,
  next_run_time TIMESTAMP,
  error_message STRING,
  updated_at TIMESTAMP DEFAULT current_timestamp()
)
USING DELTA;
```

### API Contracts

**KPIs Endpoint**:
```typescript
// GET /api/kpis?from=2024-01-01&to=2024-12-31

interface KPIResponse {
  data: {
    metric_name: string;
    dimension: string;
    dimension_value: string;
    period: string;
    value: number;
    unit: string;
  }[];
  meta: {
    from: string;
    to: string;
    total_records: number;
  };
}
```

**Jobs Endpoint**:
```typescript
// GET /api/jobs

interface JobsResponse {
  data: {
    job_id: string;
    job_name: string;
    last_run_status: 'SUCCESS' | 'FAILED' | 'RUNNING' | 'PENDING';
    last_run_time: string;
    last_run_duration_seconds: number;
    next_run_time: string;
  }[];
}
```

**Create Notion Action**:
```typescript
// POST /api/notion/actions

interface CreateActionRequest {
  project_id: string;
  title: string;
  assignee?: string;
  due_date?: string;
  source: 'advisor' | 'dq' | 'manual';
  source_id?: string;
}

interface CreateActionResponse {
  success: boolean;
  action_id: string;
  notion_url: string;
}
```

---

## Risk Mitigation

| Risk | Mitigation | Owner |
|------|------------|-------|
| Notion API rate limits | Implement caching, use webhooks | Sync Service |
| Databricks job failures | Retry logic, alerts, runbooks | Platform |
| Data quality drift | Automated DQ checks, monitoring | Data Team |
| Authentication issues | Token refresh, fallback auth | API Layer |
| Deployment failures | Rollback automation, staging | DevOps |

---

## Dependencies

### Internal

- Databricks Workspace (pre-provisioned)
- Azure Subscription (with Advisor enabled)
- Notion Integration (customer creates)

### External

- Notion API v2022-06-28
- Databricks REST API
- Azure Resource Graph API
- Azure Advisor API

---

## File Layout

```
/
├── apps/
│   └── control-room/
│       ├── src/
│       │   ├── app/
│       │   ├── components/
│       │   └── lib/
│       ├── package.json
│       ├── next.config.js
│       ├── tailwind.config.js
│       └── .env.example
├── services/
│   └── notion-sync/
│       ├── notion_sync/
│       │   ├── __init__.py
│       │   ├── sync.py
│       │   ├── client.py
│       │   └── models.py
│       ├── tests/
│       ├── pyproject.toml
│       ├── .env.example
│       └── README.md
├── infra/
│   ├── databricks/
│   │   ├── databricks.yml
│   │   ├── resources/
│   │   └── notebooks/
│   └── azure/
│       └── main.bicep
├── .github/
│   └── workflows/
│       ├── ci.yml
│       ├── deploy-control-room.yml
│       └── deploy-databricks.yml
├── .continue/
│   └── rules/
│       ├── architecture.md
│       ├── coding-standards.md
│       ├── data-contracts.md
│       └── security.md
├── docs/
│   ├── architecture.md
│   ├── runbooks.md
│   └── data-dictionary.md
├── scripts/
│   ├── dev_up.sh
│   ├── run_notion_sync.sh
│   ├── dab_deploy.sh
│   └── health_check.sh
└── spec/
    └── notion-finance-ppm-control-room/
        ├── constitution.md
        ├── prd.md
        ├── plan.md
        └── tasks.md
```

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-21 | Initial plan |
