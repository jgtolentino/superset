# Notion Finance PPM Control Room - Task Checklist

> Implementation tasks with acceptance criteria

## Overview

| Milestone | Tasks | Status |
|-----------|-------|--------|
| M1: Foundation | 5 | Pending |
| M2: Notion Sync | 6 | Pending |
| M3: Databricks Bundle | 8 | Pending |
| M4: Azure Integration | 5 | Pending |
| M5: Control Room API | 7 | Pending |
| M6: Control Room UI | 8 | Pending |
| M7: CI/CD & Deploy | 6 | Pending |
| M8: Docs & Verification | 6 | Pending |
| **Total** | **51** | - |

---

## M1: Foundation Tasks

### T1.1: Create Repository Structure

**Description**: Scaffold the monorepo directory structure

**Acceptance Criteria**:
- [ ] `apps/control-room/` directory created
- [ ] `services/notion-sync/` directory created
- [ ] `infra/databricks/` directory created
- [ ] `infra/azure/` directory created
- [ ] `.github/workflows/` directory updated
- [ ] `.continue/rules/` directory created
- [ ] `docs/` directory updated
- [ ] `scripts/` directory updated

### T1.2: Create Spec Kit Bundle

**Description**: Write all specification documents

**Acceptance Criteria**:
- [ ] `constitution.md` complete
- [ ] `prd.md` complete
- [ ] `plan.md` complete
- [ ] `tasks.md` complete

### T1.3: Set Up Continue Rules

**Description**: Create repo guardrails for code generation

**Acceptance Criteria**:
- [ ] `architecture.md` with system boundaries
- [ ] `coding-standards.md` with style rules
- [ ] `data-contracts.md` with schema definitions
- [ ] `security.md` with credential rules

### T1.4: Create .env.example Files

**Description**: Document required environment variables

**Acceptance Criteria**:
- [ ] `apps/control-room/.env.example`
- [ ] `services/notion-sync/.env.example`
- [ ] All required vars documented
- [ ] No placeholder values

### T1.5: Set Up Development Scripts

**Description**: Create scripts for local development

**Acceptance Criteria**:
- [ ] `scripts/dev_up.sh` works
- [ ] Starts local services
- [ ] Provides clear output
- [ ] Handles errors gracefully

---

## M2: Notion Sync Service Tasks

### T2.1: Create Python Package Structure

**Description**: Set up the Python package for notion-sync

**Acceptance Criteria**:
- [ ] `pyproject.toml` with dependencies
- [ ] Package structure follows best practices
- [ ] Type hints throughout
- [ ] Logging configured

### T2.2: Implement Notion API Client

**Description**: Create client for Notion API v2022-06-28

**Acceptance Criteria**:
- [ ] Authenticate with API key
- [ ] Query databases with filters
- [ ] Handle pagination (100 items/page)
- [ ] Retry logic with backoff
- [ ] Rate limit handling (3 req/sec)

### T2.3: Implement Watermark Tracking

**Description**: Track sync progress with watermarks

**Acceptance Criteria**:
- [ ] Store watermark per database
- [ ] Use `last_edited_time` as watermark
- [ ] Persist to Databricks table
- [ ] Handle first-time sync (no watermark)

### T2.4: Implement Bronze Writer

**Description**: Write raw Notion data to bronze layer

**Acceptance Criteria**:
- [ ] Connect to Databricks
- [ ] Write to `bronze.notion_raw_pages`
- [ ] Idempotent upserts by page_id
- [ ] Handle large payloads
- [ ] Batch writes for performance

### T2.5: Create Database Configuration

**Description**: Define sync configuration for each database

**Acceptance Criteria**:
- [ ] YAML config file
- [ ] Database IDs from env vars
- [ ] Sync intervals configurable
- [ ] Field mappings defined
- [ ] Validation on startup

### T2.6: Write Unit Tests

**Description**: Test coverage for sync service

**Acceptance Criteria**:
- [ ] 80% code coverage
- [ ] API client tests with mocks
- [ ] Watermark logic tests
- [ ] Writer tests
- [ ] Config validation tests

---

## M3: Databricks Bundle Tasks

### T3.1: Create DAB Configuration

**Description**: Define Databricks Asset Bundle

**Acceptance Criteria**:
- [ ] `databricks.yml` valid
- [ ] All jobs defined
- [ ] Schedules set
- [ ] Clusters configured
- [ ] Environment variables mapped

### T3.2: Create Bronze Table DDL

**Description**: Define bronze layer tables

**Acceptance Criteria**:
- [ ] `bronze.notion_raw_pages` table
- [ ] `bronze.azure_rg_raw` table
- [ ] `bronze.sync_watermarks` table
- [ ] Partitioning configured
- [ ] Delta optimization enabled

### T3.3: Implement Silver Transformations

**Description**: Transform bronze to silver layer

**Acceptance Criteria**:
- [ ] `silver.notion_programs` notebook
- [ ] `silver.notion_projects` notebook
- [ ] `silver.notion_budget_lines` notebook
- [ ] `silver.notion_risks` notebook
- [ ] `silver.notion_actions` notebook
- [ ] Type casting correct
- [ ] Null handling defined

### T3.4: Implement Gold Budget vs Actual

**Description**: Compute budget vs actual KPIs

**Acceptance Criteria**:
- [ ] Aggregate by program, project, period
- [ ] Calculate variance
- [ ] Calculate burn rate
- [ ] Historical trends preserved
- [ ] Null handling for missing data

### T3.5: Implement Gold Forecast

**Description**: Compute simple forecast projections

**Acceptance Criteria**:
- [ ] Run-rate projection
- [ ] Remaining budget calculation
- [ ] End-of-period estimates
- [ ] Confidence indicators

### T3.6: Implement Gold Project Health

**Description**: Compute project health scores

**Acceptance Criteria**:
- [ ] Risk severity aggregation
- [ ] Schedule performance
- [ ] Budget performance
- [ ] At-risk flagging
- [ ] Health score formula

### T3.7: Implement Control Room Status

**Description**: Track job run metadata

**Acceptance Criteria**:
- [ ] Query Databricks Jobs API
- [ ] Store last run status
- [ ] Store run duration
- [ ] Store error messages
- [ ] Calculate next run time

### T3.8: Create Data Quality Checks

**Description**: Implement DQ validation

**Acceptance Criteria**:
- [ ] Row count trends
- [ ] Null rate by column
- [ ] Referential integrity
- [ ] Schema drift detection
- [ ] Results to `gold.data_quality_metrics`

---

## M4: Azure Integration Tasks

### T4.1: Set Up Azure Authentication

**Description**: Configure service principal auth

**Acceptance Criteria**:
- [ ] Service principal created
- [ ] Env vars documented
- [ ] Token acquisition works
- [ ] Token refresh handled

### T4.2: Implement Resource Graph Ingestion

**Description**: Query Azure Resource Graph

**Acceptance Criteria**:
- [ ] Query all subscriptions
- [ ] Paginate results
- [ ] Store in bronze
- [ ] Handle rate limits

### T4.3: Implement Advisor Normalization

**Description**: Transform Advisor data to silver

**Acceptance Criteria**:
- [ ] Parse recommendations
- [ ] Categorize by type
- [ ] Extract impacted resources
- [ ] Calculate savings

### T4.4: Compute Advisor Gold Metrics

**Description**: Aggregate Advisor data

**Acceptance Criteria**:
- [ ] Count by category
- [ ] Total estimated savings
- [ ] Weekly trends
- [ ] Top recommendations

### T4.5: Link Advisor to Projects

**Description**: Connect recommendations to projects

**Acceptance Criteria**:
- [ ] Resource → Project mapping
- [ ] Tag-based linking
- [ ] Manual override support
- [ ] Orphan detection

---

## M5: Control Room API Tasks

### T5.1: Set Up Next.js Project

**Description**: Initialize Control Room app

**Acceptance Criteria**:
- [ ] Next.js 14+ with App Router
- [ ] TypeScript configured
- [ ] Tailwind CSS set up
- [ ] ESLint + Prettier
- [ ] shadcn/ui installed

### T5.2: Implement Databricks Client

**Description**: Client for querying Databricks

**Acceptance Criteria**:
- [ ] SQL execution API
- [ ] Token authentication
- [ ] Connection pooling
- [ ] Error handling
- [ ] Query result parsing

### T5.3: Implement Health Endpoint

**Description**: `/api/health` endpoint

**Acceptance Criteria**:
- [ ] Returns 200 when healthy
- [ ] Checks Databricks connectivity
- [ ] Returns component status
- [ ] < 100ms response time

### T5.4: Implement KPIs Endpoint

**Description**: `/api/kpis` endpoint

**Acceptance Criteria**:
- [ ] Query parameters validated
- [ ] Date range filtering
- [ ] Dimension filtering
- [ ] Aggregation options
- [ ] Pagination support

### T5.5: Implement Jobs Endpoints

**Description**: `/api/jobs` and `/api/job-runs`

**Acceptance Criteria**:
- [ ] List all jobs
- [ ] Filter by status
- [ ] Get run history
- [ ] Link to Databricks UI
- [ ] Error details exposed

### T5.6: Implement DQ Issues Endpoint

**Description**: `/api/dq/issues` endpoint

**Acceptance Criteria**:
- [ ] List active issues
- [ ] Filter by severity
- [ ] Include table/column
- [ ] Include recommendations

### T5.7: Implement Notion Actions Endpoint

**Description**: `/api/notion/actions` endpoint

**Acceptance Criteria**:
- [ ] Create action in Notion
- [ ] Link to source (advisor/dq)
- [ ] Return Notion URL
- [ ] Validate input

---

## M6: Control Room UI Tasks

### T6.1: Create Layout and Navigation

**Description**: App shell with sidebar

**Acceptance Criteria**:
- [ ] Sidebar navigation
- [ ] Header with branding
- [ ] Dark mode toggle
- [ ] Mobile responsive

### T6.2: Implement Overview Page

**Description**: `/overview` dashboard

**Acceptance Criteria**:
- [ ] KPI cards grid
- [ ] Health summary
- [ ] Recent alerts
- [ ] Quick links

### T6.3: Implement Pipelines Page

**Description**: `/pipelines` monitoring

**Acceptance Criteria**:
- [ ] Job status table
- [ ] Status indicators
- [ ] Run history modal
- [ ] Link to Databricks
- [ ] Refresh button

### T6.4: Implement Data Quality Page

**Description**: `/data-quality` dashboard

**Acceptance Criteria**:
- [ ] Issue list with severity
- [ ] Trend charts
- [ ] Filter by table
- [ ] Push-to-Notion action

### T6.5: Implement Advisor Page

**Description**: `/advisor` view

**Acceptance Criteria**:
- [ ] Category breakdown
- [ ] Recommendations list
- [ ] Savings summary
- [ ] Trend chart
- [ ] Action button

### T6.6: Implement Projects Page

**Description**: `/projects` explorer

**Acceptance Criteria**:
- [ ] Filterable table
- [ ] Search functionality
- [ ] Drill-down to detail
- [ ] Budget lines view
- [ ] Risk register view

### T6.7: Implement Charts

**Description**: Data visualizations

**Acceptance Criteria**:
- [ ] Budget vs Actual bar chart
- [ ] Burn rate line chart
- [ ] DQ trend line chart
- [ ] Advisor category pie chart
- [ ] Responsive sizing

### T6.8: Implement Mobile Responsiveness

**Description**: Mobile-friendly design

**Acceptance Criteria**:
- [ ] Sidebar collapses
- [ ] Tables scroll horizontally
- [ ] Cards stack vertically
- [ ] Touch-friendly buttons
- [ ] Tested on mobile devices

---

## M7: CI/CD & Deployment Tasks

### T7.1: Update CI Workflow

**Description**: GitHub Actions CI pipeline

**Acceptance Criteria**:
- [ ] Lint Python and TypeScript
- [ ] Run all tests
- [ ] Build Control Room
- [ ] Validate DAB bundle
- [ ] Upload artifacts

### T7.2: Create Control Room Deploy Workflow

**Description**: Deploy Control Room app

**Acceptance Criteria**:
- [ ] Build production assets
- [ ] Deploy to hosting (Vercel/Azure)
- [ ] Environment secrets
- [ ] Health check post-deploy
- [ ] Rollback on failure

### T7.3: Create Databricks Deploy Workflow

**Description**: Deploy DAB bundle

**Acceptance Criteria**:
- [ ] Authenticate to workspace
- [ ] Validate bundle
- [ ] Deploy jobs
- [ ] Run smoke test job
- [ ] Notify on completion

### T7.4: Create Infrastructure Definitions

**Description**: IaC for Azure resources

**Acceptance Criteria**:
- [ ] Bicep/Terraform templates
- [ ] Key Vault for secrets
- [ ] App Service/Container Apps
- [ ] Databricks workspace (optional)
- [ ] Deployment instructions

### T7.5: Set Up Monitoring

**Description**: Observability configuration

**Acceptance Criteria**:
- [ ] Application Insights
- [ ] Log Analytics
- [ ] Dashboard templates
- [ ] Alert rules

### T7.6: Create Alerting Rules

**Description**: Alerts for failures and SLAs

**Acceptance Criteria**:
- [ ] Job failure alerts
- [ ] API error rate alerts
- [ ] Data freshness alerts
- [ ] Notification channels

---

## M8: Documentation & Verification Tasks

### T8.1: Write Architecture Documentation

**Description**: `docs/architecture.md`

**Acceptance Criteria**:
- [ ] System overview diagram
- [ ] Component descriptions
- [ ] Data flow explanation
- [ ] Integration points
- [ ] Security model

### T8.2: Write Runbooks

**Description**: `docs/runbooks.md`

**Acceptance Criteria**:
- [ ] Incident response
- [ ] Job failure recovery
- [ ] Data quality remediation
- [ ] Scaling procedures
- [ ] Backup and restore

### T8.3: Write Data Dictionary

**Description**: `docs/data-dictionary.md`

**Acceptance Criteria**:
- [ ] All tables documented
- [ ] Column descriptions
- [ ] Data types
- [ ] Relationships
- [ ] Example queries

### T8.4: Create dev_up.sh Script

**Description**: Local development setup

**Acceptance Criteria**:
- [ ] Start Control Room
- [ ] Mock API data
- [ ] Environment validation
- [ ] Clear instructions

### T8.5: Create health_check.sh Script

**Description**: Production health verification

**Acceptance Criteria**:
- [ ] Check API health
- [ ] Check data freshness
- [ ] Check job status
- [ ] Return exit code

### T8.6: Create dab_deploy.sh Script

**Description**: Databricks deployment script

**Acceptance Criteria**:
- [ ] Validate environment
- [ ] Deploy bundle
- [ ] Run validation job
- [ ] Report status

---

## Quality Gates

### Per-Task Gates

- [ ] Code review approved
- [ ] Tests passing
- [ ] Documentation updated
- [ ] No hardcoded secrets
- [ ] Follows coding standards

### Per-Milestone Gates

- [ ] All tasks complete
- [ ] Integration tests passing
- [ ] Security review (if applicable)
- [ ] Documentation complete

### Launch Gates

- [ ] All milestones complete
- [ ] E2E tests passing
- [ ] Performance targets met
- [ ] Security review passed
- [ ] Runbooks tested
- [ ] Rollback tested

---

## Success Criteria

### Quantitative

- [ ] Sync lag < 15 minutes
- [ ] API p99 < 500ms
- [ ] Job success rate > 99%
- [ ] Data quality score > 95%
- [ ] Test coverage > 80%

### Qualitative

- [ ] All pages functional
- [ ] Documentation complete
- [ ] Scripts work end-to-end
- [ ] Ready for production

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-21 | Initial tasks |
