# Superset PostgreSQL-Native Production Deployment

Production-grade Apache Superset with PostgreSQL metadata database and example datasets.

## Quick Start

```bash
# Clone repository
git clone https://github.com/jgtolentino/superset.git
cd superset

# Set environment variables
export BASE_URL="https://superset.insightpulseai.net"
export SUPERSET_ADMIN_USER="your_admin_user"
export SUPERSET_ADMIN_PASS="your_admin_password"
export EXAMPLES_DB_URI="postgresql+psycopg2://USER:PASS@HOST:PORT/DB?options=-csearch_path%3Dexamples"
export SQLALCHEMY_DATABASE_URI="postgresql+psycopg2://USER:PASS@HOST:PORT/DB"

# Bootstrap examples
./scripts/bootstrap_examples_db.sh

# Validate setup
./scripts/validate.sh

# Run UI smoke tests (optional)
npm install
npx playwright test
```

## What This Provides

### Critical Production Fix
✅ **Resolves SQLite "database is locked" errors** in multi-worker environments
✅ **Configures Superset to use PostgreSQL metadata DB** (not SQLite) via `SUPERSET__SQLALCHEMY_DATABASE_URI`
✅ **Credential domain separation** - [SUPERSET_LOGIN] vs [DATA_DB] vs [METADATA_DB]

**Note**: Setting metadata DB URI to Postgres creates a **fresh metadata database**. You must recreate admin users and reconnect data sources. This does NOT migrate existing SQLite metadata - it's a fresh start.

### Automation Scripts
- **scripts/bootstrap_examples_db.sh** - Idempotent database + dataset creation
- **scripts/validate.sh** - Comprehensive health checks (7 validation steps including metadata DB engine check)
- **playwright/smoke.spec.ts** - Headless UI tests with screenshots

### Production Configuration
- **infra/docker/superset_config.py** - Production Superset config (Postgres metadata)
- **.github/workflows/ci.yml** - CI with linting, security checks, Playwright tests

### Documentation
- **docs/README.md** - Complete deployment guide
- All secrets stored as env vars (never hardcoded)
- Evidence outputs in `artifacts/` directory

## Key Features

1. **Idempotent** - Safe to run bootstrap multiple times
2. **Evidence-Based** - All validations return exit codes + logs
3. **Execution-First** - Scripts do the work, not manual console instructions
4. **Security-Hardened** - No secrets in repo, grep denylist in CI

## Expected Output

### Bootstrap Script (Sample)
```
=== Superset Examples Bootstrap ===
✅ Authenticated successfully
✅ Database already exists (id=2)
✅ Dataset birth_names already exists
✅ Dataset flights already exists
✅ Dataset channels already exists
=== ✅ Bootstrap Complete ===
```

### Validation Suite (Sample)
```
✅ Health check passed (HTTP 200)
✅ Authentication successful
✅ Database exists (id=2)
✅ Dataset birth_names exists (id=1)
✅ Dataset flights exists (id=2)
✅ Dataset channels exists (id=3)
✅ All 3 datasets found
=== ✅ All Validation Checks Passed ===
```

**Note**: Run `make validate` in your environment to produce actual verification evidence.

## Directory Structure

```
.
├── scripts/               # Bootstrap + validate automation
│   ├── bootstrap_examples_db.sh
│   └── validate.sh
├── infra/
│   └── docker/           # Production Superset config
│       └── superset_config.py
├── playwright/           # Headless UI tests
│   └── smoke.spec.ts
├── docs/                 # Deployment guide
│   └── README.md
├── .github/workflows/    # CI pipeline
│   └── ci.yml
└── artifacts/            # Test outputs (gitignored)
```

## Environment Variables

### Required
- `BASE_URL` - Superset instance URL
- `SUPERSET_ADMIN_USER` - Admin username
- `SUPERSET_ADMIN_PASS` - Admin password
- `EXAMPLES_DB_URI` - Data connection (Supabase examples schema)
- `SUPERSET__SQLALCHEMY_DATABASE_URI` - Metadata DB connection (Postgres, NOT SQLite)
  - Alternative: `SQLALCHEMY_DATABASE_URI` (fallback, less widely supported)

### Optional
- `REDIS_HOST` - For caching/results backend
- `SMTP_HOST` - For email notifications

## License

Apache-2.0
