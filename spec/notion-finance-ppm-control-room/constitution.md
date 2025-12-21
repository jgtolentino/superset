# Notion Finance PPM Control Room - Constitution

> Governing principles for the integrated Finance PPM system with Notion, Databricks, and Control Room UI.

## Purpose

The Notion Finance PPM Control Room is a production-ready system that bridges **Notion** (as the planning UI and source-of-truth for initiatives) with **Databricks** (as the computation and lakehouse layer) to deliver real-time finance and PPM metrics through a custom **Control Room** web application.

---

## Core Principles

### 1. Source-of-Truth Principle

**Notion is the authoritative source for all planning data.**

| Data Type | Source | Direction |
|-----------|--------|-----------|
| Programs, Projects, Workstreams | Notion | Notion → Databricks |
| Budget lines, Risks, Actions | Notion | Notion → Databricks |
| Computed KPIs, Metrics | Databricks | Databricks → Control Room |
| Pipeline health, Job status | Databricks | Databricks → Control Room |
| Azure Advisor signals | Azure | Azure → Databricks → Control Room |

**Rationale**: Single source of truth eliminates data conflicts and ensures auditability.

### 2. Medallion Architecture Principle

**All data flows through bronze → silver → gold layers.**

| Layer | Purpose | Retention |
|-------|---------|-----------|
| Bronze | Raw ingestion, full payloads | 90 days |
| Silver | Normalized, typed, validated | 1 year |
| Gold | Curated marts, KPIs, ready for consumption | Indefinite |

**Rationale**: Medallion architecture provides data lineage, recoverability, and clear transformation stages.

### 3. Idempotency Principle

**Every sync and transformation is idempotent and restartable.**

- Upserts keyed by `notion_page_id` + `database_id`
- Watermark-based incremental processing (`last_edited_time`)
- Soft deletes (archived flag) rather than hard deletes
- No side effects on repeated runs

**Rationale**: Idempotency ensures reliability, enables retries, and prevents data corruption.

### 4. Zero-Secrets-in-Code Principle

**All credentials must come from environment or secret stores.**

```yaml
rule: no_hardcoded_secrets
enforcement: hard_block
rationale: Security and compliance requirement
```

**Required Environment Variables**:
- `NOTION_API_KEY` - Notion integration token
- `DATABRICKS_HOST` - Databricks workspace URL
- `DATABRICKS_TOKEN` - Databricks access token
- `AZURE_SUBSCRIPTION_ID` - Azure subscription
- `AZURE_TENANT_ID` - Azure tenant
- `AZURE_CLIENT_ID` - Service principal ID
- `AZURE_CLIENT_SECRET` - Service principal secret

### 5. Observability Principle

**Every component must be observable and debuggable.**

- Structured logging with correlation IDs
- Job run metadata persisted to Delta tables
- Health endpoints for all services
- Data quality metrics tracked over time
- Alerting on failures and SLA breaches

**Rationale**: Observable systems are maintainable systems.

### 6. Graceful Degradation Principle

**System must remain functional when components are unavailable.**

| Component Down | Behavior |
|----------------|----------|
| Notion API | Use cached data, retry with backoff |
| Databricks | Control Room shows stale data warning |
| Azure Advisor | Skip advisor signals, continue PPM sync |
| Control Room UI | API remains available for other consumers |

---

## Non-Negotiables

### 1. No Placeholders in Production

```yaml
rule: no_placeholders
description: All configuration must be complete and functional
enforcement: hard_block
rationale: Placeholders cause production failures
```

### 2. Environment Validation Before Execution

```yaml
rule: preflight_check
description: All scripts must validate environment before running
enforcement: hard_requirement
rationale: Fail fast with clear errors
```

### 3. Evidence-Based Verification

```yaml
rule: evidence_required
description: All "success" claims must show real output
enforcement: soft_requirement
rationale: No false success claims
```

### 4. Incremental Data Processing

```yaml
rule: incremental_sync
description: Never full-refresh when incremental is possible
enforcement: hard_requirement
rationale: Efficiency and performance
```

### 5. Audit Trail

```yaml
rule: audit_trail
description: All data changes must be traceable
enforcement: hard_requirement
rationale: Compliance and debugging
```

---

## Scope Definition

### In Scope

| Component | Responsibility |
|-----------|----------------|
| Notion Sync Service | Pull data from Notion, store in bronze |
| Databricks Jobs | Transform bronze → silver → gold |
| Control Room UI | Display KPIs, health, actions |
| Azure Advisor Ingestion | Pull recommendations, store in lakehouse |
| CI/CD Pipelines | Deploy, test, validate |

### Out of Scope

| Component | Reason |
|-----------|--------|
| Notion UI | Existing platform, not customized |
| Databricks UI | Existing platform, accessed directly |
| Azure Portal | Existing platform, read-only integration |
| Authentication provider | Use existing SSO/OAuth |

---

## Data Contracts

### Notion → Bronze

```json
{
  "page_id": "uuid",
  "database_id": "uuid",
  "last_edited_time": "ISO8601",
  "properties": {},
  "raw_payload": {},
  "synced_at": "ISO8601"
}
```

### Bronze → Silver (Example: Projects)

```json
{
  "project_id": "uuid",
  "program_id": "uuid",
  "name": "string",
  "budget_total": "decimal",
  "currency": "string",
  "start_date": "date",
  "end_date": "date",
  "status": "enum",
  "priority": "enum",
  "is_archived": "boolean",
  "last_modified": "timestamp"
}
```

### Gold KPI Schema

```json
{
  "metric_name": "string",
  "dimension": "string",
  "dimension_value": "string",
  "period": "date",
  "value": "decimal",
  "unit": "string",
  "computed_at": "timestamp"
}
```

---

## Decision Matrix

### When to Sync

```
IF page.last_edited_time > watermark.last_synced_time:
    SYNC page
    UPDATE watermark

IF database.has_new_pages:
    SYNC new_pages
    UPDATE watermark
```

### When to Compute KPIs

```
IF bronze.has_new_data:
    RUN silver_transform
    RUN gold_compute

IF schedule.is_due:
    RUN gold_compute
    REFRESH materialized_views
```

### When to Alert

```
IF job.status == "FAILED":
    ALERT on_call
    LOG error

IF data_freshness > threshold:
    WARN in_control_room
    ALERT if_critical
```

---

## Quality Standards

### Code Quality

- Python: Black formatting, type hints, mypy strict
- TypeScript: ESLint + Prettier, strict mode
- SQL: SQLFluff, consistent naming

### Testing Requirements

- Unit tests: 80% coverage minimum
- Integration tests: All sync paths
- Contract tests: API endpoints
- Smoke tests: Post-deployment

### Documentation Requirements

- Architecture diagrams current
- Data dictionary complete
- Runbooks for common operations
- Troubleshooting guides maintained

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Sync lag (Notion → Gold) | < 15 minutes |
| API response time (p99) | < 500ms |
| Data quality score | > 95% |
| Job success rate | > 99% |
| Uptime (Control Room) | > 99.5% |

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-21 | Initial constitution |
