# Notion x Finance PPM - Runbooks

## Table of Contents
1. [Daily Operations](#daily-operations)
2. [Notion Sync Operations](#notion-sync-operations)
3. [Databricks Operations](#databricks-operations)
4. [Control Room Operations](#control-room-operations)
5. [Incident Response](#incident-response)
6. [Maintenance Procedures](#maintenance-procedures)

---

## Daily Operations

### Morning Health Check

**Frequency**: Daily at 9:00 AM

**Procedure**:
```bash
# Run system health check
./scripts/health_check.sh

# Expected output:
# ===================================
#  PPM System Health Check
# ===================================
#   Checking API reachable... OK
#   Health status: healthy
# ...
```

**If checks fail**:
1. Check environment variables are set
2. Verify network connectivity to services
3. Review Databricks job logs
4. Escalate if unresolved after 15 minutes

### Data Freshness Verification

**Frequency**: Daily

**Procedure**:
```sql
-- Check last sync times
SELECT
  database_id,
  last_synced_at,
  DATEDIFF(CURRENT_TIMESTAMP(), last_synced_at) as hours_since_sync
FROM main.bronze.notion_sync_watermarks
ORDER BY last_synced_at DESC;

-- Alert if any database > 24 hours stale
```

**Threshold**: Alert if `hours_since_sync > 24`

---

## Notion Sync Operations

### Run Manual Sync

**When**: On-demand or after Notion data updates

**Procedure**:
```bash
cd services/notion-sync
source .venv/bin/activate

# Incremental sync (default)
notion-sync sync

# Full refresh (all data)
notion-sync sync --full-refresh

# Sync specific database only
notion-sync sync -d <database_id>
```

### Troubleshoot Sync Failures

**Symptom**: Sync job fails or returns errors

**Diagnosis Steps**:

1. **Check credentials**:
```bash
./scripts/require_env.sh
# Should show all required variables are set
```

2. **Verify Notion API access**:
```bash
curl -s -H "Authorization: Bearer $NOTION_API_KEY" \
     -H "Notion-Version: 2022-06-28" \
     "https://api.notion.com/v1/users/me"
# Should return user info
```

3. **Check rate limiting**:
```bash
# Review logs for 429 errors
grep "429" /var/log/notion-sync/*.log
```

4. **Verify database permissions**:
   - Open Notion integration settings
   - Ensure databases are shared with integration

**Resolution**:
- Rate limit: Reduce concurrency or wait
- Auth error: Regenerate integration token
- Permission error: Re-share databases with integration

### Reset Sync Watermarks

**When**: After data corruption or to force full refresh

**Procedure**:
```sql
-- View current watermarks
SELECT * FROM main.bronze.notion_sync_watermarks;

-- Reset specific database watermark
UPDATE main.bronze.notion_sync_watermarks
SET last_synced_at = '2000-01-01T00:00:00Z'
WHERE database_id = '<database_id>';

-- Reset all watermarks (force full refresh)
TRUNCATE TABLE main.bronze.notion_sync_watermarks;
```

Then run sync:
```bash
notion-sync sync --full-refresh
```

---

## Databricks Operations

### Deploy Databricks Bundle

**When**: After code changes to notebooks or jobs

**Procedure**:
```bash
# Deploy to development
./scripts/dab_deploy.sh dev

# Deploy to staging (requires approval)
./scripts/dab_deploy.sh staging

# Deploy to production (requires approval)
./scripts/dab_deploy.sh prod
```

### Run Individual Job

**Procedure**:
```bash
cd infra/databricks

# List available jobs
databricks bundle run -t dev --list

# Run specific job
databricks bundle run -t dev notion_sync_bronze
databricks bundle run -t dev silver_transformations
databricks bundle run -t dev gold_aggregations
```

### View Job Logs

**Via CLI**:
```bash
# Get recent runs
databricks jobs list-runs --job-id <job_id> --limit 5

# Get run details
databricks runs get --run-id <run_id>

# Get run output
databricks runs get-output --run-id <run_id>
```

**Via UI**:
1. Navigate to Databricks workspace
2. Go to Workflows > Jobs
3. Click job name > View runs
4. Click run to see logs

### Troubleshoot Failed Jobs

**Symptom**: Job shows FAILED status

**Diagnosis**:

1. **Check run logs**:
```bash
databricks runs get --run-id <run_id> --output JSON | jq '.state'
```

2. **Common errors and fixes**:

| Error | Cause | Fix |
|-------|-------|-----|
| `CLUSTER_STARTUP_FAILURE` | Cluster failed to start | Check cluster config, retry |
| `DRIVER_UNREACHABLE` | Cluster lost | Retry the run |
| `DATA_LOSS` | Delta table issue | Restore from time travel |
| `PERMISSION_DENIED` | Missing access | Check Unity Catalog grants |

3. **Retry the job**:
```bash
databricks jobs run-now --job-id <job_id>
```

### Restore Data from Time Travel

**When**: Accidental data deletion or corruption

**Procedure**:
```sql
-- View table history
DESCRIBE HISTORY main.silver.projects;

-- Query data at previous version
SELECT * FROM main.silver.projects VERSION AS OF 5;

-- Query data at previous timestamp
SELECT * FROM main.silver.projects TIMESTAMP AS OF '2024-01-15 10:00:00';

-- Restore table to previous version
RESTORE TABLE main.silver.projects TO VERSION AS OF 5;
```

---

## Control Room Operations

### Start Development Server

**Procedure**:
```bash
cd apps/control-room

# Install dependencies (first time)
npm install

# Start development server
npm run dev

# Access at http://localhost:3000
```

### Deploy Control Room

**Staging**:
```bash
# Triggered automatically on PR merge to main
# Or manually via GitHub Actions
gh workflow run deploy-control-room.yml -f environment=staging
```

**Production**:
```bash
# Requires manual approval
gh workflow run deploy-control-room.yml -f environment=production
```

### Troubleshoot UI Issues

**Symptom**: Page shows error or no data

**Diagnosis**:

1. **Check API health**:
```bash
curl http://localhost:3000/api/health
# Should return {"status": "healthy", ...}
```

2. **Check Databricks connectivity**:
```bash
curl http://localhost:3000/api/kpis
# Should return KPI data or mock data
```

3. **Enable mock data** (for local dev):
```bash
# In .env.local
MOCK_DATA=true
```

4. **Check browser console** for JavaScript errors

**Resolution**:
- Connection error: Verify `DATABRICKS_*` env vars
- Auth error: Regenerate Databricks token
- No data: Check that gold tables are populated

---

## Incident Response

### P1 - Complete Outage

**Symptoms**: Control Room unreachable, all jobs failing

**Response Time**: 15 minutes

**Procedure**:
1. Check infrastructure status (cloud provider)
2. Verify network connectivity
3. Check Databricks workspace status
4. Review recent deployments for rollback candidates
5. Engage on-call engineer

### P2 - Partial Degradation

**Symptoms**: Some features unavailable, stale data

**Response Time**: 1 hour

**Procedure**:
1. Identify affected component (sync, transformation, UI)
2. Check component-specific logs
3. Re-run failed jobs if applicable
4. Apply temporary workaround
5. Create ticket for root cause analysis

### P3 - Data Quality Issue

**Symptoms**: Incorrect metrics, missing records

**Response Time**: 4 hours

**Procedure**:
1. Query `main.gold.data_quality_issues` for details
2. Identify source (Notion, transformation, aggregation)
3. Fix data at source if possible
4. Re-run transformation pipeline
5. Verify fix in Control Room UI

### Escalation Matrix

| Severity | Response Time | Escalation |
|----------|---------------|------------|
| P1 | 15 min | On-call → Manager → Director |
| P2 | 1 hour | On-call → Manager |
| P3 | 4 hours | On-call |
| P4 | Next day | Backlog |

---

## Maintenance Procedures

### Weekly: Cleanup Old Runs

**Procedure**:
```sql
-- Delete runs older than 30 days
DELETE FROM main.bronze.notion_raw_pages
WHERE synced_at < CURRENT_DATE() - INTERVAL 30 DAY
  AND NOT EXISTS (
    SELECT 1 FROM main.silver.projects p
    WHERE p.notion_page_id = notion_raw_pages.page_id
  );

-- Vacuum Delta tables
VACUUM main.bronze.notion_raw_pages RETAIN 168 HOURS;
VACUUM main.silver.projects RETAIN 168 HOURS;
-- Repeat for all tables
```

### Monthly: Review Access

**Procedure**:
1. Audit Notion integration permissions
2. Rotate Databricks tokens if >90 days old
3. Review Azure Service Principal permissions
4. Check for unused API keys

### Quarterly: Capacity Review

**Procedure**:
1. Review data volume growth trends
2. Analyze job run times for optimization
3. Review cluster sizing and costs
4. Plan capacity for next quarter

### Credential Rotation

**Notion API Key**:
1. Generate new integration token in Notion
2. Update in secret store (GitHub, DigitalOcean)
3. Redeploy affected services
4. Revoke old token after verification

**Databricks Token**:
1. Generate new PAT in Databricks
2. Update in CI/CD secrets
3. Update local `.env` files
4. Verify connectivity before revoking old token

**Azure Service Principal**:
1. Create new client secret in Azure AD
2. Update in secret store
3. Redeploy notebooks
4. Delete old secret after verification

---

## Appendix

### Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `NOTION_API_KEY` | Yes | Notion integration token |
| `DATABRICKS_HOST` | Yes | Workspace URL |
| `DATABRICKS_TOKEN` | Yes | Personal access token |
| `DATABRICKS_HTTP_PATH` | No | SQL warehouse path |
| `DATABRICKS_CATALOG` | No | Unity Catalog name (default: main) |
| `AZURE_TENANT_ID` | No | Azure AD tenant |
| `AZURE_CLIENT_ID` | No | Service principal ID |
| `AZURE_CLIENT_SECRET` | No | Service principal secret |
| `AZURE_SUBSCRIPTION_ID` | No | Azure subscription |

### Contact Information

| Role | Contact |
|------|---------|
| On-Call Engineer | #ppm-oncall Slack channel |
| Data Platform Team | data-platform@company.com |
| Security Team | security@company.com |
