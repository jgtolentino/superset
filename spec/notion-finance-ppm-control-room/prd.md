# Notion Finance PPM Control Room - Product Requirements Document

> Version 1.0.0 | December 2025

## Executive Summary

The Notion Finance PPM Control Room is an integrated platform that combines Notion's project/program management capabilities with Databricks' data lakehouse to deliver real-time finance and PPM metrics through a custom "Control Room" web application styled after Azure Advisor.

### Problem Statement

Organizations using Notion for PPM lack:

1. **Real-time Financial Visibility** - Budget vs. actual data is scattered across databases
2. **Pipeline Health Monitoring** - No unified view of data synchronization health
3. **Data Quality Assurance** - Manual checking of data integrity
4. **Actionable Recommendations** - Azure Advisor signals not connected to project data
5. **Centralized Control Plane** - Multiple tools with no single pane of glass

### Solution

A fully integrated system that:
- Syncs Notion project/program data to Databricks lakehouse
- Computes finance/PPM KPIs in gold layer marts
- Ingests Azure Advisor recommendations for cost/risk optimization
- Provides a Control Room UI for health, KPIs, data quality, and actions

---

## Target Users

### 1. Finance Controllers

**Profile**: Responsible for budget tracking and financial reporting

**Needs**:
- Real-time budget vs. actual visibility
- Variance analysis by program/project
- Burn rate and forecast projections
- Export capabilities for reporting

**Use Case**: "I need to see which projects are over budget this quarter"

### 2. Program Managers

**Profile**: Oversee multiple projects and initiatives

**Needs**:
- Portfolio health overview
- Risk register visibility
- Schedule performance indicators
- Cross-project dependencies

**Use Case**: "I need to identify at-risk projects before they become critical"

### 3. Data Engineers / Platform Ops

**Profile**: Maintain data pipelines and infrastructure

**Needs**:
- Pipeline health monitoring
- Job run status and history
- Data quality metrics
- Alerting and incident response

**Use Case**: "I need to know immediately when a sync job fails"

### 4. Cloud Architects / FinOps

**Profile**: Optimize cloud spending and infrastructure

**Needs**:
- Azure Advisor recommendations
- Cost optimization signals
- Security and reliability insights
- Action tracking from recommendations

**Use Case**: "I need to see all Azure cost savings opportunities linked to projects"

---

## Functional Requirements

### FR-1: Notion Data Sync

**Priority**: P0 (Critical)

The system must synchronize data from Notion databases to Databricks.

| Database | Key Fields | Sync Frequency |
|----------|------------|----------------|
| Programs | name, owner, dates, status | 5 min |
| Projects | program, name, budget, dates, status, priority | 5 min |
| BudgetLines | project, category, vendor, amounts, dates | 5 min |
| Risks | project, severity, probability, status, mitigation | 5 min |
| Actions | project, title, assignee, due, status, source | 5 min |

**Acceptance Criteria**:
- [ ] Incremental sync using `last_edited_time` watermark
- [ ] Idempotent upserts by `page_id` + `database_id`
- [ ] Soft delete handling (archived pages)
- [ ] Full payload stored in bronze, normalized in silver
- [ ] Sync lag < 10 minutes under normal load

### FR-2: Medallion Layer Processing

**Priority**: P0 (Critical)

Data must flow through bronze → silver → gold layers.

**Bronze Layer**:
```
bronze.notion_raw_pages
├── page_id (string)
├── database_id (string)
├── last_edited_time (timestamp)
├── properties (json)
├── raw_payload (json)
├── synced_at (timestamp)
└── _ingestion_timestamp (timestamp)
```

**Silver Layer**:
```
silver.notion_programs
silver.notion_projects
silver.notion_budget_lines
silver.notion_risks
silver.notion_actions
```

**Gold Layer**:
```
gold.ppm_budget_vs_actual
gold.ppm_forecast
gold.ppm_project_health
gold.azure_advisor_recs
gold.control_room_status
```

**Acceptance Criteria**:
- [ ] Bronze retains raw data for 90 days
- [ ] Silver normalized with proper types
- [ ] Gold marts optimized for dashboard queries
- [ ] Data lineage traceable across layers

### FR-3: Finance KPIs

**Priority**: P0 (Critical)

System must compute standard finance/PPM metrics.

| KPI | Calculation | Dimensions |
|-----|-------------|------------|
| Budget Total | SUM(budget_lines.amount) | program, project, period |
| Actuals YTD | SUM(budget_lines.actual_amount) WHERE paid_date < today | program, project, period |
| Variance | Actuals - Budget | program, project, period |
| Burn Rate | Actuals / days_elapsed | project, period |
| CPI | EV / AC (simplified) | project |
| SPI | EV / PV (simplified) | project |

**Acceptance Criteria**:
- [ ] All KPIs computed daily
- [ ] Historical trends retained
- [ ] Drill-down capability by dimension
- [ ] Null handling for missing data

### FR-4: Azure Advisor Integration

**Priority**: P1 (High)

System must ingest Azure Advisor recommendations.

**Data Source**: Azure Resource Graph API

**Recommendation Categories**:
- Cost (rightsizing, reserved instances)
- Security (vulnerability fixes)
- Reliability (HA configurations)
- Operational Excellence (best practices)
- Performance (scaling recommendations)

**Acceptance Criteria**:
- [ ] Daily ingestion of recommendations
- [ ] Store in bronze, normalize to silver
- [ ] Compute summary metrics in gold
- [ ] Link to impacted resources/projects where possible

### FR-5: Control Room UI

**Priority**: P0 (Critical)

Web application with the following pages:

**`/overview`** - Dashboard home
- KPI cards: total budget, actuals YTD, variance, burn rate, at-risk projects count
- Health summary: last successful run, failing jobs, data freshness
- Quick links to detail pages

**`/pipelines`** - Pipeline monitoring
- Job list with status indicators
- Last run time and duration
- Link to Databricks run logs
- Error filtering and search

**`/data-quality`** - Data quality dashboard
- Row count trends by table
- Schema drift detection
- Null rate by key columns
- Referential integrity checks
- Issue list with push-to-Notion action

**`/advisor`** - Azure Advisor view
- Recommendations by category
- Impacted resources
- Estimated savings
- Weekly trend chart

**`/projects`** - Project explorer
- Filterable project table
- Drill-down to budget lines
- Risk register view
- Forecast projection

**Acceptance Criteria**:
- [ ] All pages functional and styled
- [ ] Response time < 2s for all pages
- [ ] Mobile-responsive design
- [ ] Dark mode support

### FR-6: API Layer

**Priority**: P0 (Critical)

REST API for Control Room and external consumers.

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/health` | GET | Service health check |
| `/api/kpis` | GET | Retrieve KPI data |
| `/api/jobs` | GET | List Databricks jobs |
| `/api/job-runs` | GET | Job run history |
| `/api/dq/issues` | GET | Data quality issues |
| `/api/notion/actions` | POST | Create Notion action |
| `/api/advisor/recommendations` | GET | Azure Advisor data |

**Acceptance Criteria**:
- [ ] OpenAPI 3.0 spec documented
- [ ] Authentication via API key or JWT
- [ ] Rate limiting (100 req/min)
- [ ] Structured error responses
- [ ] < 500ms p99 response time

---

## Non-Functional Requirements

### NFR-1: Performance

| Metric | Target |
|--------|--------|
| Sync lag (end-to-end) | < 15 minutes |
| API response (p50) | < 200ms |
| API response (p99) | < 500ms |
| Page load time | < 3s |
| Job execution time | < 5 min per job |

### NFR-2: Reliability

| Metric | Target |
|--------|--------|
| Control Room uptime | > 99.5% |
| Job success rate | > 99% |
| Data freshness SLA | < 30 min |
| Recovery time (RTO) | < 1 hour |
| Recovery point (RPO) | < 1 hour |

### NFR-3: Security

| Requirement | Implementation |
|-------------|----------------|
| Authentication | JWT/OAuth 2.0 |
| Authorization | RBAC with roles |
| Secrets | Azure Key Vault / env vars |
| Encryption at rest | Databricks managed keys |
| Encryption in transit | TLS 1.3 |
| Audit logging | All API calls logged |

### NFR-4: Scalability

| Dimension | Target |
|-----------|--------|
| Notion databases | 10 DBs, 10K pages each |
| Concurrent users | 100 |
| API requests/min | 1000 |
| Data retention | 1 year silver, indefinite gold |

---

## User Stories

### US-1: View Budget vs. Actual

**As a** Finance Controller
**I want** to see budget vs. actual by program
**So that** I can identify variances and take action

**Acceptance Criteria**:
- [ ] Overview shows total budget, actuals, variance
- [ ] Drill-down by program shows projects
- [ ] Drill-down by project shows budget lines
- [ ] Export to CSV available

### US-2: Monitor Pipeline Health

**As a** Data Engineer
**I want** to see all job statuses in one view
**So that** I can quickly identify and resolve failures

**Acceptance Criteria**:
- [ ] All jobs listed with current status
- [ ] Failed jobs highlighted in red
- [ ] Click to view job details
- [ ] Link to Databricks run page

### US-3: Track Azure Advisor Recommendations

**As a** FinOps Engineer
**I want** to see Azure cost optimization opportunities
**So that** I can prioritize savings initiatives

**Acceptance Criteria**:
- [ ] Recommendations grouped by category
- [ ] Estimated savings displayed
- [ ] Create Notion action from recommendation
- [ ] Track recommendation status over time

### US-4: Identify At-Risk Projects

**As a** Program Manager
**I want** to see projects with health issues
**So that** I can intervene before they become critical

**Acceptance Criteria**:
- [ ] At-risk projects flagged
- [ ] Risk score visible
- [ ] Drill-down to specific risks
- [ ] Mitigation status tracked

---

## System Integration

### Integration Map

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Notion    │────▶│ Sync Service│────▶│  Databricks │
│ (Planning)  │     │  (Python)   │     │ (Lakehouse) │
└─────────────┘     └─────────────┘     └──────┬──────┘
                                                │
┌─────────────┐                                 │
│    Azure    │─────────────────────────────────┤
│   Advisor   │                                 │
└─────────────┘                                 │
                                                ▼
                    ┌─────────────┐     ┌─────────────┐
                    │ Control Room│◀────│    API      │
                    │    (UI)     │     │  (FastAPI)  │
                    └─────────────┘     └─────────────┘
```

---

## Success Metrics

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Time to insight | 4 hours | 15 min | Sync lag monitoring |
| Manual reporting effort | 10 hrs/week | 2 hrs/week | User survey |
| Data quality issues | Unknown | > 95% pass rate | DQ dashboard |
| Cost savings identified | $0 | $50K/quarter | Advisor tracking |
| User satisfaction | N/A | > 85% | Survey |

---

## Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Notion API rate limits | Medium | High | Caching, incremental sync |
| Databricks availability | High | Low | Retry logic, alerts |
| Azure API changes | Medium | Low | Version pinning, monitoring |
| Data quality issues | High | Medium | DQ checks, validation |
| Scope creep | Medium | Medium | Clear PRD, phased delivery |

---

## Dependencies

| Dependency | Type | Owner |
|------------|------|-------|
| Notion Integration | External | Customer Notion admin |
| Databricks Workspace | Infrastructure | Platform team |
| Azure Subscription | Infrastructure | Cloud team |
| DNS/SSL Certificates | Infrastructure | Platform team |

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2025-12-21 | Claude | Initial PRD |
