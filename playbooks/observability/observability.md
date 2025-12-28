# Observability & Audit

Everything is traceable:
- DB migrations version
- Bundle hash (plan sha256)
- Workspace target (dev/staging/prod)
- Export snapshots (ui_exports/<env>/)
- PR linkage for UI-first changes

## Source References

- Claude Cookbooks: `observability/` directory
- Claude Cookbooks: `tool_evaluation/` directory

## Required artifacts

| Artifact | Location | Purpose |
|----------|----------|---------|
| Runtime export | `.hybrid/exports/<env>/` | Current state snapshot |
| Committed export | `ui_exports/<env>/` | Normalized for Git |
| Diff inputs | `.hybrid/normalized/...` | Drift detection |
| Deployment manifest | `meta.deployments` table | Version tracking |

## Deployment Manifest

Track what's running in each environment:

```sql
-- Query current state
SELECT git_sha, migration_version, bundle_hash, deployed_at
FROM meta.deployments
WHERE environment = 'prod'
ORDER BY deployed_at DESC
LIMIT 1;
```

## Drift Posture

| Environment | Default Behavior | Override |
|-------------|-----------------|----------|
| dev | Warn on drift | `--force` |
| staging | Fail on drift | `--force` |
| prod | Fail on drift | Requires approval |

## Checks

```bash
# Check for drift
hybrid drift-plan --env dev

# Count exported files
find ui_exports/dev -type f | wc -l

# Verify deployment manifest
psql "$DATABASE_URL" -c "SELECT * FROM meta.deployments ORDER BY deployed_at DESC LIMIT 5"
```

## Logging Standards

All operations must log:
1. Start time
2. Environment
3. Git SHA
4. Bundle hash
5. Result (success/failure)
6. Duration

## Applies to

- `scripts/sync_env.sh`
- `scripts/export_to_pr.sh`
- `docs/spec/**/*`
