# Data Contracts

> Schema definitions and data contracts for the Notion Finance PPM Control Room

## Overview

All data flows through the medallion architecture with strict contracts at each layer:

```
Notion API → Bronze → Silver → Gold → API → UI
```

Changes to schemas require:
1. Update this document
2. Migration script if breaking
3. Downstream consumer notification

---

## Bronze Layer Contracts

### bronze.notion_raw_pages

Raw Notion page data as-is from the API.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| page_id | STRING | NO | Notion page UUID |
| database_id | STRING | NO | Notion database UUID |
| database_name | STRING | YES | Friendly name (programs, projects, etc.) |
| last_edited_time | TIMESTAMP | NO | From Notion API |
| properties | MAP<STRING, STRING> | YES | Flattened properties |
| raw_payload | STRING | NO | Full JSON payload |
| synced_at | TIMESTAMP | NO | When we fetched it |
| _ingestion_timestamp | TIMESTAMP | NO | Databricks ingestion time |

**Partitioning**: `database_name`
**Primary Key**: `(page_id, database_id)`

### bronze.azure_rg_raw

Raw Azure Resource Graph query results.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| resource_id | STRING | NO | Full Azure resource ID |
| resource_type | STRING | YES | e.g., Microsoft.Compute/virtualMachines |
| resource_group | STRING | YES | Resource group name |
| subscription_id | STRING | YES | Subscription GUID |
| location | STRING | YES | Azure region |
| tags | MAP<STRING, STRING> | YES | Resource tags |
| properties | STRING | NO | Full JSON properties |
| advisor_recommendations | STRING | YES | JSON array of recommendations |
| ingested_at | TIMESTAMP | NO | Ingestion timestamp |

**Primary Key**: `resource_id`

### bronze.sync_watermarks

Tracks sync progress per database.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| database_id | STRING | NO | Notion database UUID |
| database_name | STRING | YES | Friendly name |
| last_synced_time | TIMESTAMP | NO | Last `last_edited_time` processed |
| last_sync_run | TIMESTAMP | NO | When sync job ran |
| pages_synced | BIGINT | YES | Count of pages in last run |

**Primary Key**: `database_id`

---

## Silver Layer Contracts

### silver.notion_programs

Normalized program data.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| program_id | STRING | NO | Notion page ID |
| name | STRING | NO | Program name |
| owner | STRING | YES | Owner name or email |
| start_date | DATE | YES | Program start |
| end_date | DATE | YES | Program end |
| status | STRING | YES | active, completed, on_hold, cancelled |
| description | STRING | YES | Program description |
| is_archived | BOOLEAN | NO | Soft delete flag |
| last_modified | TIMESTAMP | NO | From Notion |
| synced_at | TIMESTAMP | NO | When normalized |

**Primary Key**: `program_id`

### silver.notion_projects

Normalized project data.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| project_id | STRING | NO | Notion page ID |
| program_id | STRING | YES | FK to programs |
| name | STRING | NO | Project name |
| budget_total | DECIMAL(18,2) | YES | Total planned budget |
| currency | STRING | NO | ISO currency code (default: USD) |
| start_date | DATE | YES | Project start |
| end_date | DATE | YES | Project end |
| status | STRING | YES | planning, active, completed, on_hold, cancelled |
| priority | STRING | YES | high, medium, low |
| owner | STRING | YES | PM name or email |
| is_archived | BOOLEAN | NO | Soft delete flag |
| last_modified | TIMESTAMP | NO | From Notion |
| synced_at | TIMESTAMP | NO | When normalized |

**Primary Key**: `project_id`
**Foreign Keys**: `program_id → silver.notion_programs.program_id`

### silver.notion_budget_lines

Individual budget line items.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| budget_line_id | STRING | NO | Notion page ID |
| project_id | STRING | NO | FK to projects |
| category | STRING | YES | CapEx, OpEx |
| subcategory | STRING | YES | e.g., Hardware, Software, Labor |
| vendor | STRING | YES | Vendor name |
| description | STRING | YES | Line description |
| amount | DECIMAL(18,2) | YES | Planned amount |
| currency | STRING | NO | ISO currency code |
| committed_date | DATE | YES | When committed |
| invoice_date | DATE | YES | When invoiced |
| paid_date | DATE | YES | When paid |
| actual_amount | DECIMAL(18,2) | YES | Actual spent |
| notes | STRING | YES | Additional notes |
| is_archived | BOOLEAN | NO | Soft delete flag |
| last_modified | TIMESTAMP | NO | From Notion |
| synced_at | TIMESTAMP | NO | When normalized |

**Primary Key**: `budget_line_id`
**Foreign Keys**: `project_id → silver.notion_projects.project_id`

### silver.notion_risks

Risk register entries.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| risk_id | STRING | NO | Notion page ID |
| project_id | STRING | NO | FK to projects |
| title | STRING | NO | Risk title |
| description | STRING | YES | Full description |
| severity | STRING | YES | critical, high, medium, low |
| probability | STRING | YES | high, medium, low |
| impact | STRING | YES | high, medium, low |
| status | STRING | YES | open, mitigated, accepted, closed |
| mitigation | STRING | YES | Mitigation plan |
| owner | STRING | YES | Risk owner |
| due_date | DATE | YES | Mitigation due date |
| is_archived | BOOLEAN | NO | Soft delete flag |
| last_modified | TIMESTAMP | NO | From Notion |
| synced_at | TIMESTAMP | NO | When normalized |

**Primary Key**: `risk_id`
**Foreign Keys**: `project_id → silver.notion_projects.project_id`

### silver.notion_actions

Action items (from Advisor, DQ, or manual).

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| action_id | STRING | NO | Notion page ID |
| project_id | STRING | YES | FK to projects (optional) |
| title | STRING | NO | Action title |
| description | STRING | YES | Full description |
| assignee | STRING | YES | Assigned to |
| due_date | DATE | YES | Due date |
| status | STRING | YES | todo, in_progress, done, cancelled |
| source | STRING | YES | advisor, dq, manual |
| source_id | STRING | YES | Reference to source recommendation |
| priority | STRING | YES | high, medium, low |
| is_archived | BOOLEAN | NO | Soft delete flag |
| last_modified | TIMESTAMP | NO | From Notion |
| synced_at | TIMESTAMP | NO | When normalized |

**Primary Key**: `action_id`
**Foreign Keys**: `project_id → silver.notion_projects.project_id`

### silver.azure_advisor_recommendations

Normalized Azure Advisor data.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| recommendation_id | STRING | NO | Azure recommendation ID |
| resource_id | STRING | NO | Impacted resource |
| category | STRING | NO | Cost, Security, Reliability, OperationalExcellence, Performance |
| impact | STRING | YES | High, Medium, Low |
| impacted_field | STRING | YES | Specific field impacted |
| impacted_value | STRING | YES | Current value |
| short_description | STRING | YES | Brief description |
| extended_properties | STRING | YES | JSON with details |
| estimated_savings | DECIMAL(18,2) | YES | Monthly savings (USD) |
| ingested_at | TIMESTAMP | NO | When ingested |

**Primary Key**: `recommendation_id`

---

## Gold Layer Contracts

### gold.ppm_budget_vs_actual

Aggregated budget metrics.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| metric_id | STRING | NO | Generated UUID |
| metric_name | STRING | NO | budget, actual, variance, burn_rate |
| dimension | STRING | NO | program, project, category, all |
| dimension_value | STRING | NO | Dimension ID or 'total' |
| period | DATE | NO | First day of period |
| period_type | STRING | NO | day, week, month, quarter, year |
| value | DECIMAL(18,2) | YES | Metric value |
| unit | STRING | NO | USD, percent, ratio |
| computed_at | TIMESTAMP | NO | When computed |

**Primary Key**: `metric_id`
**Partition By**: `period`

### gold.ppm_forecast

Budget forecasts.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| forecast_id | STRING | NO | Generated UUID |
| project_id | STRING | NO | FK to projects |
| forecast_date | DATE | NO | Date of forecast |
| forecast_type | STRING | NO | run_rate, regression, manual |
| remaining_budget | DECIMAL(18,2) | YES | Budget - Actuals to date |
| projected_spend | DECIMAL(18,2) | YES | Projected total at end |
| projected_variance | DECIMAL(18,2) | YES | Projected over/under |
| confidence | STRING | YES | high, medium, low |
| computed_at | TIMESTAMP | NO | When computed |

**Primary Key**: `forecast_id`

### gold.ppm_project_health

Project health scores.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| project_id | STRING | NO | FK to projects |
| health_date | DATE | NO | Score date |
| overall_score | DECIMAL(5,2) | YES | 0-100 score |
| budget_score | DECIMAL(5,2) | YES | Budget health 0-100 |
| schedule_score | DECIMAL(5,2) | YES | Schedule health 0-100 |
| risk_score | DECIMAL(5,2) | YES | Risk health 0-100 |
| status | STRING | YES | healthy, at_risk, critical |
| risk_count | INT | YES | Open risks count |
| open_actions | INT | YES | Open action items |
| computed_at | TIMESTAMP | NO | When computed |

**Primary Key**: `(project_id, health_date)`

### gold.azure_advisor_summary

Aggregated Advisor metrics.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| summary_date | DATE | NO | Summary date |
| category | STRING | NO | Advisor category |
| recommendation_count | INT | YES | Count of recommendations |
| impacted_resources | INT | YES | Unique resources |
| total_estimated_savings | DECIMAL(18,2) | YES | Sum of savings |
| high_impact_count | INT | YES | High impact items |
| computed_at | TIMESTAMP | NO | When computed |

**Primary Key**: `(summary_date, category)`

### gold.control_room_status

Job and pipeline status.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| job_id | STRING | NO | Databricks job ID |
| job_name | STRING | NO | Friendly name |
| job_type | STRING | YES | sync, transform, compute |
| last_run_id | STRING | YES | Last run ID |
| last_run_status | STRING | YES | SUCCESS, FAILED, RUNNING, PENDING |
| last_run_start | TIMESTAMP | YES | Run start time |
| last_run_end | TIMESTAMP | YES | Run end time |
| last_run_duration_seconds | INT | YES | Duration |
| next_scheduled_run | TIMESTAMP | YES | Next run time |
| error_message | STRING | YES | Last error if failed |
| updated_at | TIMESTAMP | NO | Record update time |

**Primary Key**: `job_id`

### gold.data_quality_metrics

Data quality measurements.

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| metric_id | STRING | NO | Generated UUID |
| check_date | DATE | NO | Check date |
| table_name | STRING | NO | Full table name |
| check_type | STRING | NO | row_count, null_rate, schema_drift, referential |
| column_name | STRING | YES | Column if applicable |
| expected_value | STRING | YES | Expected result |
| actual_value | STRING | YES | Actual result |
| passed | BOOLEAN | NO | Pass/fail |
| severity | STRING | YES | critical, warning, info |
| details | STRING | YES | JSON details |
| computed_at | TIMESTAMP | NO | When checked |

**Primary Key**: `metric_id`

---

## API Response Contracts

### KPIs Response

```typescript
interface KPIResponse {
  data: {
    metric_name: string;
    dimension: string;
    dimension_value: string;
    period: string;  // YYYY-MM-DD
    value: number;
    unit: string;
  }[];
  meta: {
    from: string;
    to: string;
    total_records: number;
    computed_at: string;
  };
}
```

### Jobs Response

```typescript
interface JobsResponse {
  data: {
    job_id: string;
    job_name: string;
    job_type: string;
    last_run_status: 'SUCCESS' | 'FAILED' | 'RUNNING' | 'PENDING';
    last_run_start: string | null;
    last_run_end: string | null;
    last_run_duration_seconds: number | null;
    next_scheduled_run: string | null;
    error_message: string | null;
  }[];
}
```

### Data Quality Issues Response

```typescript
interface DQIssuesResponse {
  data: {
    metric_id: string;
    check_date: string;
    table_name: string;
    check_type: string;
    column_name: string | null;
    expected_value: string | null;
    actual_value: string | null;
    severity: 'critical' | 'warning' | 'info';
    details: Record<string, unknown> | null;
  }[];
}
```

### Create Action Request

```typescript
interface CreateActionRequest {
  project_id?: string;
  title: string;
  description?: string;
  assignee?: string;
  due_date?: string;  // YYYY-MM-DD
  source: 'advisor' | 'dq' | 'manual';
  source_id?: string;
  priority?: 'high' | 'medium' | 'low';
}

interface CreateActionResponse {
  success: boolean;
  action_id: string;
  notion_url: string;
}
```

---

## Schema Evolution Rules

### Additive Changes (Non-breaking)

- Adding new nullable columns
- Adding new tables
- Adding new API response fields

### Breaking Changes (Require Migration)

- Removing columns
- Changing column types
- Renaming tables/columns
- Changing primary keys

### Migration Process

1. Create migration notebook in `infra/databricks/notebooks/migrations/`
2. Test in dev workspace
3. Update data-contracts.md
4. Update API DTOs
5. Deploy migration before code changes
6. Verify downstream consumers
