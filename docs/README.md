# Superset PostgreSQL-Native Production Setup

Production-grade Apache Superset deployment with PostgreSQL metadata DB and example datasets.

## Quick Start

### One-Command Bootstrap

```bash
# Set environment variables
export BASE_URL="https://superset.insightpulseai.net"
export SUPERSET_ADMIN_USER="[SUPERSET_LOGIN_USER]"
export SUPERSET_ADMIN_PASS="[SUPERSET_LOGIN_PASS]"
export EXAMPLES_DB_URI="[DATA_DB_URI]"
export SQLALCHEMY_DATABASE_URI="[METADATA_DB_URI]"

# Bootstrap examples database and datasets
./scripts/bootstrap_examples_db.sh

# Validate setup
./scripts/validate.sh

# Run UI smoke tests (requires Playwright installed)
npx playwright test playwright/smoke.spec.ts
```

## Credential Domains

**CRITICAL**: These are separate credential sets - DO NOT mix them!

### [SUPERSET_LOGIN] - Superset Web UI Credentials
- **Username**: `SUPERSET_ADMIN_USER` environment variable
- **Password**: `SUPERSET_ADMIN_PASS` environment variable
- **Purpose**: Login to Superset at BASE_URL
- **Stored in**: Superset metadata database
- **Managed via**: `superset fab create-admin`

### [DATA_DB] - Supabase PostgreSQL Data Connection
- **Connection URI**: `EXAMPLES_DB_URI` environment variable
- **Format**: `postgresql+psycopg2://USER:PASS@HOST:PORT/DB?options=-csearch_path%3Dexamples`
- **Purpose**: Superset queries `examples` schema tables (birth_names, flights, channels)
- **Stored in**: Superset database connections
- **Get from**: Supabase → Settings → Database → Connection String (Session Pooler)

### [METADATA_DB] - Superset Metadata Database
- **Connection URI**: `SQLALCHEMY_DATABASE_URI` environment variable
- **Format**: `postgresql+psycopg2://USER:PASS@HOST:PORT/DB`
- **Purpose**: Stores Superset configuration, users, dashboards, logs
- **MUST BE PostgreSQL**: SQLite causes "database is locked" errors in production

## Directory Structure

```
.
├── scripts/                    # Automation scripts
│   ├── bootstrap_examples_db.sh  # Idempotent setup
│   └── validate.sh                # Validation suite
├── infra/
│   ├── docker/                    # Docker configs
│   │   └── superset_config.py     # Production config (Postgres metadata)
│   └── k8s/                       # Kubernetes manifests (future)
├── playwright/                    # UI smoke tests
│   └── smoke.spec.ts
├── docs/                          # Documentation
│   └── README.md                  # This file
└── artifacts/                     # Gitignored test outputs
    ├── ui-home.png
    └── ui-databases.png
```

## Evidence Outputs

All validation and test evidence is written to `artifacts/`:

- `ui-home.png` - Homepage screenshot
- `ui-databases.png` - Databases page screenshot
- `ui-databases-search.png` - Database search results

## SQLite to PostgreSQL Migration

**Problem**: Production Superset using SQLite for metadata causes:
```
sqlite3.OperationalError: database is locked
during INSERT INTO logs (... action='test_connection_attempt' ...)
```

**Solution**: Use `infra/docker/superset_config.py` which sets:

```python
SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI', ...)
```

**Deployment Steps**:

1. **Set metadata DB environment variable**:
   ```bash
   export SQLALCHEMY_DATABASE_URI="postgresql+psycopg2://USER:PASS@HOST:PORT/DB"
   ```

2. **Initialize Postgres metadata schema**:
   ```bash
   superset db upgrade
   superset init
   ```

3. **Recreate admin user** (if needed):
   ```bash
   superset fab create-admin \
     --username "$SUPERSET_ADMIN_USER" \
     --firstname Admin \
     --lastname User \
     --email admin@example.com \
     --password "$SUPERSET_ADMIN_PASS"
   ```

4. **Verify no SQLite usage**:
   ```bash
   # Should return 0 matches
   find /app -name "*.db" -type f 2>/dev/null | grep -c superset
   ```

## CI/CD Integration

GitHub Actions workflow validates:
- Shell script syntax (shellcheck)
- No secrets in codebase (grep denylist)
- Optional: Playwright smoke tests (if secrets configured)

## Troubleshooting

### "database is locked" Error
**Symptom**: `sqlite3.OperationalError: database is locked`

**Fix**: Verify `SQLALCHEMY_DATABASE_URI` points to PostgreSQL (not SQLite)

```bash
# In production environment
env | grep SQLALCHEMY_DATABASE_URI
# Should show: postgresql+psycopg2://...
# NOT: sqlite:///...
```

### Authentication Failed
**Symptom**: HTTP 401 from `/api/v1/security/login`

**Fix**: Verify credentials:
```bash
echo "User: $SUPERSET_ADMIN_USER (redacted length: ${#SUPERSET_ADMIN_PASS} chars)"
curl -X POST "$BASE_URL/api/v1/security/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$SUPERSET_ADMIN_USER\",\"password\":\"$SUPERSET_ADMIN_PASS\",\"provider\":\"db\"}"
```

### Database Not Found
**Symptom**: "Examples (Postgres)" database missing

**Fix**: Re-run bootstrap script:
```bash
./scripts/bootstrap_examples_db.sh
```

### Playwright Tests Fail
**Symptom**: Screenshots missing or tests timeout

**Fix**: Install Playwright browsers:
```bash
npx playwright install chromium
```

## Security

**Never commit**:
- Real credentials (`[SUPERSET_LOGIN_USER]`, `[SUPERSET_LOGIN_PASS]`)
- Database URIs with passwords (`[DATA_DB_URI]`, `[METADATA_DB_URI]`)
- Tokens or API keys

**Always use**:
- Environment variables for secrets
- Placeholders in documentation
- `.gitignore` for `artifacts/` directory
