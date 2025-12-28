# Git-First Sync Protocol for Hybrid Control Plane

> One source of truth (Git). Everything else is derived + continuously reconciled.

## The Sync Model

### Source of Truth (Repo)

| Component | Location | Authoritative |
|-----------|----------|---------------|
| DB schema | `db/migrations/` | SQL migrations |
| BI assets | `assets/**/*.yaml.j2` | Jinja2 templates |
| Docs | `docs/` | Generated + committed |

### Derived / Runtime

| Component | Source | Reconciliation |
|-----------|--------|----------------|
| Local runtime | docker-compose | Rebuilt from repo |
| Server runtime | Apply from bundle | Never manually patched |

---

## Canonical Repo Structure

```
preset-hybrid/
├── assets/                     # Templated Superset assets (*.yaml.j2)
│   ├── databases/
│   ├── datasets/
│   ├── charts/
│   └── dashboards/
├── bundles/                    # Compiled per env (generated)
│   ├── dev/
│   ├── staging/
│   └── prod/
├── env/                        # Env vars for templating
│   ├── dev.yaml
│   ├── staging.yaml
│   └── prod.yaml
├── mappings/                   # Retarget rules (optional)
│   └── prod-schema-map.yaml
├── ui_exports/                 # Normalized runtime exports (committed)
│   └── .gitkeep
├── db/
│   ├── migrations/             # SQL migrations (source of truth)
│   │   ├── 001_init.sql
│   │   ├── 002_add_invoices.sql
│   │   └── ...
│   └── schema_dump/            # Generated schema snapshots (committed)
│       ├── schema.sql
│       └── dbmate_status.txt
├── docs/
│   ├── db/                     # Generated DB docs (committed)
│   │   └── SCHEMA.md
│   └── bi/                     # Generated BI docs (committed)
│       └── ASSETS.md
├── scripts/
│   ├── db_sync.sh              # Migrate + dump schema
│   ├── db_drift_check.sh       # Compare runtime vs repo
│   ├── docs_gen.sh             # Generate docs from schema + assets
│   ├── export_to_pr.sh         # Runtime → repo PR loop
│   └── sync_env.sh             # One-command full sync
├── .github/
│   └── workflows/
│       ├── pr-check.yml        # Validate on PR
│       └── deploy.yml          # Apply on merge
└── Makefile
```

---

## Hard Rule: Only Two Ways Changes Enter Main

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CODE-FIRST                                                                 │
│  ──────────                                                                 │
│  Edit db/migrations/* or assets/*                                          │
│       ↓                                                                     │
│  CI validates + applies                                                     │
│       ↓                                                                     │
│  Runtime updates                                                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  UI-FIRST                                                                   │
│  ────────                                                                   │
│  Edit in Superset/Preset UI                                                 │
│       ↓                                                                     │
│  export_to_pr.sh opens PR                                                   │
│       ↓                                                                     │
│  PR merged                                                                  │
│       ↓                                                                     │
│  translate turns exports → templates                                        │
│       ↓                                                                     │
│  CI applies                                                                 │
└─────────────────────────────────────────────────────────────────────────────┘

Anything else = DRIFT (blocked by CI)
```

---

## Scripts

### 1. DB Sync: Migrate + Dump Schema

```bash
#!/usr/bin/env bash
# scripts/db_sync.sh
set -euo pipefail

: "${DATABASE_URL:?Set DATABASE_URL}"

# Apply migrations
dbmate up

# Dump schema snapshot (schema-only, stable)
mkdir -p db/schema_dump
pg_dump "$DATABASE_URL" --schema-only --no-owner --no-privileges > db/schema_dump/schema.sql

# Store applied migration version in marker file
dbmate status > db/schema_dump/dbmate_status.txt

echo "DB_OK"
```

### 2. DB Drift Check: Compare Runtime vs Repo

```bash
#!/usr/bin/env bash
# scripts/db_drift_check.sh
set -euo pipefail

: "${DATABASE_URL:?Set DATABASE_URL}"

tmp="$(mktemp -d)"
pg_dump "$DATABASE_URL" --schema-only --no-owner --no-privileges > "$tmp/runtime.sql"

if diff -u db/schema_dump/schema.sql "$tmp/runtime.sql" >/dev/null; then
  echo "NO_DB_DRIFT"
else
  echo "DB_DRIFT_FOUND"
  diff -u db/schema_dump/schema.sql "$tmp/runtime.sql" | head -n 200
  exit 1
fi
```

### 3. Docs Generation: Schema + Assets

```bash
#!/usr/bin/env bash
# scripts/docs_gen.sh
set -euo pipefail

mkdir -p docs/db docs/bi

# DB docs: render schema.sql into markdown
python3 - <<'PY'
from pathlib import Path
schema = Path("db/schema_dump/schema.sql").read_text(encoding="utf-8")
out = Path("docs/db/SCHEMA.md")
out.write_text("# Database Schema (generated)\n\n```sql\n" + schema + "\n```\n", encoding="utf-8")
print(f"Generated: {out}")
PY

# BI docs: inventory assets
python3 - <<'PY'
from pathlib import Path
import glob
out = Path("docs/bi/ASSETS.md")
lines = ["# BI Assets (generated)\n"]
for kind in ["databases","datasets","charts","dashboards"]:
    files = sorted(glob.glob(f"assets/{kind}/*"))
    lines.append(f"## {kind}\n")
    for f in files:
        lines.append(f"- `{f}`")
    lines.append("")
out.write_text("\n".join(lines), encoding="utf-8")
print(f"Generated: {out}")
PY

echo "DOCS_OK"
```

### 4. Full Sync: One Command to Rule Them All

```bash
#!/usr/bin/env bash
# scripts/sync_env.sh
set -euo pipefail

ENV="${1:-dev}"

# ---- REQUIRED ENV VARS ----
: "${DATABASE_URL:?Set DATABASE_URL}"

echo "=== 1) DB migrate + snapshot ==="
./scripts/db_sync.sh

echo "=== 2) Compile + validate BI bundle ==="
hybrid compile --env "$ENV"
hybrid validate --env "$ENV"

echo "=== 3) Drift checks (fail fast) ==="
./scripts/db_drift_check.sh
hybrid drift-plan --env "$ENV"  # Remove '|| true' for strict mode

echo "=== 4) Apply BI assets to runtime ==="
hybrid apply --env "$ENV"

echo "=== 5) Re-check BI drift (should be clean) ==="
hybrid drift-plan --env "$ENV"

echo "=== 6) Generate docs ==="
./scripts/docs_gen.sh

echo "SYNC_DONE ($ENV)"
```

---

## Makefile

```makefile
.PHONY: sync-dev sync-staging sync-prod export-dev export-prod docs drift

# Full sync commands
sync-dev:
	DATABASE_URL=$(DEV_DATABASE_URL) ./scripts/sync_env.sh dev

sync-staging:
	DATABASE_URL=$(STAGING_DATABASE_URL) ./scripts/sync_env.sh staging

sync-prod:
	DATABASE_URL=$(PROD_DATABASE_URL) ./scripts/sync_env.sh prod

# Export from runtime to PR
export-dev:
	./scripts/export_to_pr.sh dev

export-prod:
	./scripts/export_to_pr.sh prod

# Generate docs only
docs:
	./scripts/docs_gen.sh

# Check drift only
drift:
	./scripts/db_drift_check.sh
	hybrid drift-plan --env $(ENV)

# Local development
local-up:
	docker-compose up -d
	sleep 5
	DATABASE_URL=postgres://superset:superset@localhost:5432/superset ./scripts/db_sync.sh
	hybrid apply --env dev

local-down:
	docker-compose down -v
```

---

## CI Enforcement

### PR Check Workflow

```yaml
# .github/workflows/pr-check.yml
name: PR Check

on:
  pull_request:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install tools
        run: |
          pip install preset-cli
          curl -fsSL https://github.com/amacneil/dbmate/releases/latest/download/dbmate-linux-amd64 -o /usr/local/bin/dbmate
          chmod +x /usr/local/bin/dbmate

      - name: Compile and validate BI assets
        run: |
          hybrid compile --env dev
          hybrid validate --env dev

      - name: Regenerate docs
        run: ./scripts/docs_gen.sh

      - name: Check for uncommitted changes
        run: |
          git diff --exit-code
          # Fails if docs or schema dumps changed but not committed
```

### Deploy Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy-staging:
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v4

      - name: Setup tools
        run: |
          pip install preset-cli
          curl -fsSL https://github.com/amacneil/dbmate/releases/latest/download/dbmate-linux-amd64 -o /usr/local/bin/dbmate
          chmod +x /usr/local/bin/dbmate

      - name: Apply DB migrations
        env:
          DATABASE_URL: ${{ secrets.STAGING_DATABASE_URL }}
        run: dbmate up

      - name: Apply BI assets
        env:
          SUPERSET_URL: ${{ secrets.STAGING_SUPERSET_URL }}
          SUPERSET_TOKEN: ${{ secrets.STAGING_SUPERSET_TOKEN }}
        run: |
          hybrid compile --env staging
          hybrid apply --env staging

      - name: Verify no drift
        run: hybrid drift-plan --env staging

  deploy-prod:
    needs: deploy-staging
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Setup tools
        run: |
          pip install preset-cli
          curl -fsSL https://github.com/amacneil/dbmate/releases/latest/download/dbmate-linux-amd64 -o /usr/local/bin/dbmate
          chmod +x /usr/local/bin/dbmate

      - name: Apply DB migrations
        env:
          DATABASE_URL: ${{ secrets.PROD_DATABASE_URL }}
        run: dbmate up

      - name: Apply BI assets
        env:
          SUPERSET_URL: ${{ secrets.PROD_SUPERSET_URL }}
          SUPERSET_TOKEN: ${{ secrets.PROD_SUPERSET_TOKEN }}
        run: |
          hybrid compile --env prod
          hybrid apply --env prod

      - name: Verify no drift
        run: hybrid drift-plan --env prod
```

---

## Operational Truth Table

| Symptom | Detection | Resolution |
|---------|-----------|------------|
| Runtime differs from repo assets | `hybrid drift-plan` shows diff | `make export-dev` (UI-first) OR `hybrid apply` (Git wins) |
| DB differs from migrations | `db_drift_check.sh` fails | Add migration OR stop ad-hoc DDL |
| Docs differ from schema/assets | `git diff` after `docs_gen.sh` | Commit generated docs |
| Local out of sync | `make local-up` fails | `make local-down && make local-up` |

---

## Advanced: Runtime Manifest

For instant "what version is prod running?", add a manifest to both DB and Superset:

### DB Table

```sql
-- db/migrations/999_add_deployment_manifest.sql
CREATE SCHEMA IF NOT EXISTS meta;

CREATE TABLE meta.deployments (
    id SERIAL PRIMARY KEY,
    git_sha VARCHAR(40) NOT NULL,
    migration_version VARCHAR(255) NOT NULL,
    bundle_hash VARCHAR(64) NOT NULL,
    environment VARCHAR(50) NOT NULL,
    deployed_at TIMESTAMPTZ DEFAULT NOW(),
    deployed_by VARCHAR(255)
);

CREATE INDEX idx_deployments_env ON meta.deployments(environment);
```

### Update on Deploy

```bash
# Add to scripts/sync_env.sh after apply step
GIT_SHA=$(git rev-parse HEAD)
BUNDLE_HASH=$(sha256sum bundles/$ENV/*.yaml | sha256sum | cut -d' ' -f1)
MIGRATION_VERSION=$(dbmate status | tail -1)

psql "$DATABASE_URL" -c "
INSERT INTO meta.deployments (git_sha, migration_version, bundle_hash, environment, deployed_by)
VALUES ('$GIT_SHA', '$MIGRATION_VERSION', '$BUNDLE_HASH', '$ENV', '$(whoami)@$(hostname)');
"
```

### Query Current State

```bash
# What version is prod running?
psql "$PROD_DATABASE_URL" -c "
SELECT git_sha, migration_version, bundle_hash, deployed_at
FROM meta.deployments
WHERE environment = 'prod'
ORDER BY deployed_at DESC
LIMIT 1;
"
```

---

## Summary: The Sealed Loop

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  GIT (Source of Truth)                                                      │
│  ─────────────────────                                                      │
│  db/migrations/  →  assets/  →  docs/                                       │
└───────────────────────────────────┬─────────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
┌───────────────────────────────┐  ┌───────────────────────────────┐
│  LOCAL RUNTIME                │  │  SERVER RUNTIME               │
│  ─────────────                │  │  ──────────────               │
│  docker-compose               │  │  Superset + DB                │
│  make local-up                │  │  CI/CD applies                │
│                               │  │                               │
│  Drift? → git diff shows it   │  │  Drift? → blocked by CI       │
└───────────────────────────────┘  └───────────────────────────────┘
                    │                               │
                    │         ┌─────────────────────┘
                    │         │
                    ▼         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  RECONCILIATION                                                             │
│  ─────────────                                                              │
│  • export_to_pr.sh (UI changes → PR)                                        │
│  • hybrid apply (Git wins)                                                  │
│  • dbmate up (migrations → runtime)                                         │
│  • docs_gen.sh (regenerate docs)                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

**The loop is sealed when:**

1. CI blocks PRs with uncommitted generated files
2. CI blocks deploys if drift detected after apply
3. All runtime changes must go through export → PR → merge → apply
