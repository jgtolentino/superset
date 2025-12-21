# Notion x Finance PPM - Data Dictionary

This document describes all tables in the PPM data lakehouse, organized by medallion layer.

## Table of Contents
- [Bronze Layer](#bronze-layer)
- [Silver Layer](#silver-layer)
- [Gold Layer](#gold-layer)
- [Data Lineage](#data-lineage)

---

## Bronze Layer

Raw data ingested from source systems with minimal transformation. All tables use Delta Lake format.

### main.bronze.notion_raw_pages

Raw Notion page data including full JSON properties.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `page_id` | STRING | Notion page UUID (PK) | `a1b2c3d4-...` |
| `database_id` | STRING | Source database UUID | `e5f6g7h8-...` |
| `title` | STRING | Page title | `"Q1 Budget Review"` |
| `properties` | STRING | Full properties JSON | `{"Status": {...}}` |
| `created_time` | TIMESTAMP | Page creation time | `2024-01-15 10:30:00` |
| `last_edited_time` | TIMESTAMP | Last modification time | `2024-01-20 14:45:00` |
| `created_by` | STRING | Creator user ID | `user-uuid` |
| `synced_at` | TIMESTAMP | When record was synced | `2024-01-21 00:00:00` |

**Partitioning**: None
**Primary Key**: `page_id`
**Update Strategy**: MERGE on `page_id`

---

### main.bronze.notion_sync_watermarks

Tracks incremental sync state per database.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `database_id` | STRING | Notion database UUID (PK) | `e5f6g7h8-...` |
| `database_name` | STRING | Human-readable name | `"Programs"` |
| `last_synced_at` | TIMESTAMP | Last successful sync time | `2024-01-21 00:00:00` |
| `last_page_count` | INT | Pages synced in last run | `150` |
| `total_pages` | INT | Total pages in database | `1250` |

**Primary Key**: `database_id`
**Update Strategy**: MERGE on `database_id`

---

### main.bronze.azure_resources

Raw Azure Resource Graph data.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `id` | STRING | Azure resource ID (PK) | `/subscriptions/.../rg/...` |
| `name` | STRING | Resource name | `"prod-sql-server"` |
| `type` | STRING | Resource type | `"Microsoft.Sql/servers"` |
| `resource_group` | STRING | Resource group name | `"rg-production"` |
| `location` | STRING | Azure region | `"eastus"` |
| `subscription_id` | STRING | Subscription UUID | `sub-uuid` |
| `tags` | STRING | Resource tags JSON | `{"env": "prod"}` |
| `properties` | STRING | Resource properties JSON | `{...}` |
| `synced_at` | TIMESTAMP | When record was synced | `2024-01-21 00:00:00` |

**Primary Key**: `id`
**Update Strategy**: MERGE on `id`

---

### main.bronze.azure_advisor

Raw Azure Advisor recommendations.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `id` | STRING | Recommendation ID (PK) | `rec-uuid` |
| `name` | STRING | Recommendation name | `"Right-size VM"` |
| `category` | STRING | Advisor category | `"Cost"` |
| `impact` | STRING | Business impact level | `"High"` |
| `impacted_field` | STRING | Affected resource field | `"Microsoft.Compute/virtualMachines"` |
| `impacted_value` | STRING | Specific resource | `"vm-oversized-01"` |
| `short_description` | STRING | Brief recommendation | `"Resize or shutdown..."` |
| `extended_properties` | STRING | Additional details JSON | `{"annualSavings": 5000}` |
| `resource_metadata` | STRING | Resource info JSON | `{...}` |
| `synced_at` | TIMESTAMP | When record was synced | `2024-01-21 00:00:00` |

**Primary Key**: `id`
**Update Strategy**: MERGE on `id`

---

## Silver Layer

Cleaned, validated, and strongly-typed data ready for analysis.

### main.silver.programs

Financial programs with budget allocation.

| Column | Type | Description | Nullable | Example |
|--------|------|-------------|----------|---------|
| `program_id` | STRING | Unique identifier (PK) | No | `PRG-001` |
| `notion_page_id` | STRING | Source Notion page ID | No | `a1b2c3d4-...` |
| `name` | STRING | Program name | No | `"Cloud Modernization"` |
| `description` | STRING | Program description | Yes | `"Multi-year initiative..."` |
| `owner` | STRING | Program owner name | Yes | `"Jane Smith"` |
| `status` | STRING | Current status | No | `"Active"` |
| `start_date` | DATE | Program start date | Yes | `2024-01-01` |
| `end_date` | DATE | Target end date | Yes | `2025-12-31` |
| `budget_total` | DECIMAL(18,2) | Total allocated budget | Yes | `5000000.00` |
| `budget_spent` | DECIMAL(18,2) | Amount spent to date | Yes | `1250000.00` |
| `currency` | STRING | Budget currency | No | `"USD"` |
| `created_at` | TIMESTAMP | Record creation time | No | `2024-01-15 10:30:00` |
| `updated_at` | TIMESTAMP | Last update time | No | `2024-01-20 14:45:00` |

**Primary Key**: `program_id`
**Foreign Keys**: None
**Indexes**: `status`, `owner`

---

### main.silver.projects

Individual projects within programs.

| Column | Type | Description | Nullable | Example |
|--------|------|-------------|----------|---------|
| `project_id` | STRING | Unique identifier (PK) | No | `PRJ-001` |
| `notion_page_id` | STRING | Source Notion page ID | No | `b2c3d4e5-...` |
| `program_id` | STRING | Parent program ID (FK) | Yes | `PRG-001` |
| `name` | STRING | Project name | No | `"API Gateway Migration"` |
| `description` | STRING | Project description | Yes | `"Migrate legacy APIs..."` |
| `owner` | STRING | Project owner name | Yes | `"John Doe"` |
| `status` | STRING | Current status | No | `"In Progress"` |
| `priority` | STRING | Priority level | Yes | `"High"` |
| `health` | STRING | Health indicator | Yes | `"Green"` |
| `start_date` | DATE | Project start date | Yes | `2024-02-01` |
| `end_date` | DATE | Target end date | Yes | `2024-06-30` |
| `budget_allocated` | DECIMAL(18,2) | Allocated budget | Yes | `250000.00` |
| `budget_spent` | DECIMAL(18,2) | Spent amount | Yes | `75000.00` |
| `percent_complete` | DECIMAL(5,2) | Completion percentage | Yes | `35.00` |
| `risk_score` | INT | Computed risk score | Yes | `15` |
| `created_at` | TIMESTAMP | Record creation time | No | `2024-01-20 09:00:00` |
| `updated_at` | TIMESTAMP | Last update time | No | `2024-01-25 16:30:00` |

**Primary Key**: `project_id`
**Foreign Keys**: `program_id` → `programs.program_id`
**Indexes**: `status`, `health`, `program_id`

---

### main.silver.budget_lines

Line-item budget entries.

| Column | Type | Description | Nullable | Example |
|--------|------|-------------|----------|---------|
| `budget_line_id` | STRING | Unique identifier (PK) | No | `BUD-001` |
| `notion_page_id` | STRING | Source Notion page ID | No | `c3d4e5f6-...` |
| `project_id` | STRING | Parent project ID (FK) | No | `PRJ-001` |
| `category` | STRING | Budget category | No | `"Personnel"` |
| `description` | STRING | Line item description | Yes | `"Senior Developer (6 mo)"` |
| `amount_planned` | DECIMAL(18,2) | Planned amount | No | `120000.00` |
| `amount_actual` | DECIMAL(18,2) | Actual spend | Yes | `95000.00` |
| `amount_forecast` | DECIMAL(18,2) | Forecast to complete | Yes | `130000.00` |
| `fiscal_year` | INT | Fiscal year | No | `2024` |
| `fiscal_quarter` | INT | Fiscal quarter (1-4) | Yes | `1` |
| `vendor` | STRING | Vendor name | Yes | `"Acme Consulting"` |
| `cost_center` | STRING | Cost center code | Yes | `"CC-4500"` |
| `created_at` | TIMESTAMP | Record creation time | No | `2024-01-15 11:00:00` |
| `updated_at` | TIMESTAMP | Last update time | No | `2024-01-28 10:15:00` |

**Primary Key**: `budget_line_id`
**Foreign Keys**: `project_id` → `projects.project_id`
**Indexes**: `project_id`, `category`, `fiscal_year`

---

### main.silver.risks

Risk register entries.

| Column | Type | Description | Nullable | Example |
|--------|------|-------------|----------|---------|
| `risk_id` | STRING | Unique identifier (PK) | No | `RSK-001` |
| `notion_page_id` | STRING | Source Notion page ID | No | `d4e5f6g7-...` |
| `project_id` | STRING | Related project ID (FK) | Yes | `PRJ-001` |
| `title` | STRING | Risk title | No | `"Vendor Delivery Delay"` |
| `description` | STRING | Detailed description | Yes | `"Primary vendor may..."` |
| `category` | STRING | Risk category | Yes | `"Schedule"` |
| `probability` | STRING | Likelihood level | Yes | `"Medium"` |
| `impact` | STRING | Impact severity | Yes | `"High"` |
| `risk_score` | INT | Computed score (1-25) | Yes | `12` |
| `status` | STRING | Current status | No | `"Open"` |
| `owner` | STRING | Risk owner | Yes | `"PM Team"` |
| `mitigation_plan` | STRING | Mitigation strategy | Yes | `"Identify backup vendor..."` |
| `due_date` | DATE | Mitigation due date | Yes | `2024-03-15` |
| `created_at` | TIMESTAMP | Record creation time | No | `2024-01-18 14:00:00` |
| `updated_at` | TIMESTAMP | Last update time | No | `2024-01-22 09:30:00` |

**Primary Key**: `risk_id`
**Foreign Keys**: `project_id` → `projects.project_id`
**Indexes**: `project_id`, `status`, `risk_score`

---

### main.silver.actions

Action items and tasks.

| Column | Type | Description | Nullable | Example |
|--------|------|-------------|----------|---------|
| `action_id` | STRING | Unique identifier (PK) | No | `ACT-001` |
| `notion_page_id` | STRING | Source Notion page ID | No | `e5f6g7h8-...` |
| `project_id` | STRING | Related project ID (FK) | Yes | `PRJ-001` |
| `title` | STRING | Action title | No | `"Review API contracts"` |
| `description` | STRING | Detailed description | Yes | `"Review and approve..."` |
| `status` | STRING | Current status | No | `"In Progress"` |
| `priority` | STRING | Priority level | Yes | `"High"` |
| `assignee` | STRING | Assigned person | Yes | `"Jane Smith"` |
| `due_date` | DATE | Due date | Yes | `2024-02-10` |
| `completed_date` | DATE | Actual completion date | Yes | `null` |
| `source` | STRING | Origin of action | Yes | `"Risk Mitigation"` |
| `created_at` | TIMESTAMP | Record creation time | No | `2024-01-20 10:00:00` |
| `updated_at` | TIMESTAMP | Last update time | No | `2024-01-28 16:00:00` |

**Primary Key**: `action_id`
**Foreign Keys**: `project_id` → `projects.project_id`
**Indexes**: `project_id`, `status`, `assignee`, `due_date`

---

### main.silver.advisor_recommendations

Typed Azure Advisor recommendations.

| Column | Type | Description | Nullable | Example |
|--------|------|-------------|----------|---------|
| `recommendation_id` | STRING | Unique identifier (PK) | No | `rec-uuid` |
| `category` | STRING | Advisor category | No | `"Cost"` |
| `impact` | STRING | Business impact | No | `"High"` |
| `resource_type` | STRING | Azure resource type | No | `"Microsoft.Compute/virtualMachines"` |
| `resource_name` | STRING | Resource name | No | `"vm-oversized-01"` |
| `resource_group` | STRING | Resource group | Yes | `"rg-production"` |
| `subscription_id` | STRING | Subscription ID | Yes | `sub-uuid` |
| `short_description` | STRING | Brief recommendation | No | `"Resize or shutdown..."` |
| `potential_savings` | DECIMAL(18,2) | Annual savings estimate | Yes | `5000.00` |
| `currency` | STRING | Savings currency | Yes | `"USD"` |
| `status` | STRING | Implementation status | No | `"Open"` |
| `synced_at` | TIMESTAMP | Last sync time | No | `2024-01-21 00:00:00` |

**Primary Key**: `recommendation_id`
**Indexes**: `category`, `impact`, `status`

---

## Gold Layer

Business-ready aggregations, KPIs, and metrics for reporting.

### main.gold.budget_vs_actual

Budget variance analysis by project and category.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `project_id` | STRING | Project identifier | `PRJ-001` |
| `project_name` | STRING | Project name | `"API Migration"` |
| `program_id` | STRING | Program identifier | `PRG-001` |
| `category` | STRING | Budget category | `"Personnel"` |
| `fiscal_year` | INT | Fiscal year | `2024` |
| `fiscal_quarter` | INT | Quarter (1-4) | `1` |
| `planned_amount` | DECIMAL(18,2) | Budgeted amount | `500000.00` |
| `actual_amount` | DECIMAL(18,2) | Actual spend | `425000.00` |
| `forecast_amount` | DECIMAL(18,2) | Forecast total | `520000.00` |
| `variance_amount` | DECIMAL(18,2) | Planned - Actual | `75000.00` |
| `variance_percent` | DECIMAL(5,2) | Variance % | `15.00` |
| `is_over_budget` | BOOLEAN | Over budget flag | `false` |
| `computed_at` | TIMESTAMP | Computation time | `2024-01-21 01:00:00` |

**Grain**: Project × Category × Quarter
**Refresh**: Daily

---

### main.gold.project_health

Project health scores and trends.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `project_id` | STRING | Project identifier | `PRJ-001` |
| `project_name` | STRING | Project name | `"API Migration"` |
| `program_id` | STRING | Program identifier | `PRG-001` |
| `health_status` | STRING | Overall health | `"Yellow"` |
| `health_score` | INT | Numeric score (0-100) | `72` |
| `schedule_score` | INT | Schedule health (0-100) | `65` |
| `budget_score` | INT | Budget health (0-100) | `80` |
| `risk_score` | INT | Risk health (0-100) | `70` |
| `quality_score` | INT | Quality health (0-100) | `75` |
| `open_risks` | INT | Count of open risks | `3` |
| `overdue_actions` | INT | Count of overdue items | `2` |
| `percent_complete` | DECIMAL(5,2) | Completion % | `45.00` |
| `days_remaining` | INT | Days to deadline | `95` |
| `trend` | STRING | Score trend | `"Improving"` |
| `computed_at` | TIMESTAMP | Computation time | `2024-01-21 01:00:00` |

**Grain**: Project
**Refresh**: Daily

---

### main.gold.forecast

Financial forecasting by project.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `project_id` | STRING | Project identifier | `PRJ-001` |
| `project_name` | STRING | Project name | `"API Migration"` |
| `fiscal_year` | INT | Forecast year | `2024` |
| `fiscal_quarter` | INT | Forecast quarter | `2` |
| `category` | STRING | Budget category | `"Personnel"` |
| `forecast_amount` | DECIMAL(18,2) | Forecast spend | `150000.00` |
| `confidence` | STRING | Confidence level | `"High"` |
| `basis` | STRING | Forecast basis | `"Trend"` |
| `computed_at` | TIMESTAMP | Computation time | `2024-01-21 01:00:00` |

**Grain**: Project × Category × Quarter
**Refresh**: Weekly

---

### main.gold.control_room_status

Unified status for Control Room dashboard.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `component` | STRING | System component | `"notion_sync"` |
| `status` | STRING | Current status | `"healthy"` |
| `last_run_at` | TIMESTAMP | Last execution time | `2024-01-21 00:00:00` |
| `last_run_status` | STRING | Last run result | `"success"` |
| `records_processed` | INT | Records in last run | `1250` |
| `error_count` | INT | Errors in last run | `0` |
| `warning_count` | INT | Warnings in last run | `5` |
| `next_scheduled_at` | TIMESTAMP | Next run time | `2024-01-22 00:00:00` |
| `message` | STRING | Status message | `"All systems operational"` |
| `computed_at` | TIMESTAMP | Last update time | `2024-01-21 01:00:00` |

**Grain**: Component
**Refresh**: Every 15 minutes

---

### main.gold.advisor_summary

Aggregated Azure Advisor recommendations.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `category` | STRING | Advisor category | `"Cost"` |
| `impact` | STRING | Impact level | `"High"` |
| `recommendation_count` | INT | Number of recs | `15` |
| `affected_resources` | INT | Unique resources | `12` |
| `total_savings` | DECIMAL(18,2) | Potential savings | `45000.00` |
| `currency` | STRING | Savings currency | `"USD"` |
| `top_resource_type` | STRING | Most common type | `"VirtualMachines"` |
| `computed_at` | TIMESTAMP | Computation time | `2024-01-21 01:00:00` |

**Grain**: Category × Impact
**Refresh**: Daily

---

### main.gold.data_quality_issues

Data quality check results.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `issue_id` | STRING | Unique identifier | `DQ-001` |
| `check_name` | STRING | Check that failed | `"Null Budget Check"` |
| `table_name` | STRING | Affected table | `"silver.projects"` |
| `column_name` | STRING | Affected column | `"budget_allocated"` |
| `severity` | STRING | Issue severity | `"Warning"` |
| `category` | STRING | Issue category | `"Completeness"` |
| `record_count` | INT | Affected records | `5` |
| `sample_values` | STRING | Example values | `["PRJ-005", "PRJ-012"]` |
| `description` | STRING | Issue description | `"5 projects missing budget"` |
| `detected_at` | TIMESTAMP | When detected | `2024-01-21 01:00:00` |
| `resolved_at` | TIMESTAMP | When resolved | `null` |
| `status` | STRING | Issue status | `"Open"` |

**Grain**: Issue
**Refresh**: After each transformation run

---

## Data Lineage

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           SOURCE SYSTEMS                                 │
└─────────────┬───────────────────────────────────────┬───────────────────┘
              │                                       │
              ▼                                       ▼
┌─────────────────────────┐             ┌─────────────────────────┐
│   Notion API            │             │   Azure APIs            │
│   - Programs DB         │             │   - Resource Graph      │
│   - Projects DB         │             │   - Advisor             │
│   - Budget Lines DB     │             │                         │
│   - Risks DB            │             │                         │
│   - Actions DB          │             │                         │
└───────────┬─────────────┘             └───────────┬─────────────┘
            │                                       │
            ▼                                       ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            BRONZE LAYER                                  │
├─────────────────────────┬─────────────────────────┬─────────────────────┤
│  notion_raw_pages       │  azure_resources        │  azure_advisor      │
│  notion_sync_watermarks │                         │                     │
└───────────┬─────────────┴───────────┬─────────────┴─────────────────────┘
            │                         │
            ▼                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            SILVER LAYER                                  │
├──────────┬──────────┬─────────────┬───────┬─────────┬───────────────────┤
│ programs │ projects │ budget_lines│ risks │ actions │ advisor_recs      │
└────┬─────┴────┬─────┴──────┬──────┴───┬───┴────┬────┴────────┬──────────┘
     │          │            │          │        │             │
     ▼          ▼            ▼          ▼        ▼             ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                             GOLD LAYER                                   │
├───────────────────┬─────────────────┬──────────────┬────────────────────┤
│ budget_vs_actual  │ project_health  │ forecast     │ control_room_status│
│ advisor_summary   │ data_quality    │              │                    │
└───────────────────┴─────────────────┴──────────────┴────────────────────┘
```

### Transformation Dependencies

| Gold Table | Silver Dependencies | Transformation |
|------------|---------------------|----------------|
| budget_vs_actual | projects, budget_lines | Aggregate by project/quarter |
| project_health | projects, risks, actions | Compute weighted scores |
| forecast | budget_lines, projects | Trend extrapolation |
| control_room_status | (all silver tables) | Status aggregation |
| advisor_summary | advisor_recommendations | Category aggregation |
| data_quality_issues | (all silver tables) | Rule-based checks |

### Refresh Schedule

| Layer | Frequency | Trigger |
|-------|-----------|---------|
| Bronze | Every 4 hours | Scheduled job |
| Silver | After Bronze | Job dependency |
| Gold | After Silver | Job dependency |

### Data Retention

| Layer | Retention | Notes |
|-------|-----------|-------|
| Bronze | 30 days | Time travel enabled |
| Silver | Indefinite | Current + history |
| Gold | 1 year | Archived quarterly |
