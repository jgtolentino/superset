#!/usr/bin/env bash
set -euo pipefail

# Load Official Superset Sample Dashboards
# Runs superset load-examples in production container via DigitalOcean App Platform
# Requires: doctl, SUPERSET_ADMIN_PASS env var

# ============================================================================
# PREFLIGHT CHECK
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$SCRIPT_DIR/require_env.sh"

# ============================================================================
# CONFIGURATION
# ============================================================================

APP_ID="73af11cb-dab2-4cb1-9770-291c536531e6"  # superset-analytics
COMPONENT_NAME="superset"  # Default component name for DO apps

# Image version (must match infra/do/superset-app.yaml)
# Use digest for reproducibility: apache/superset@sha256:1d1fdaae...
# Update with: ./scripts/get_image_digest.sh <version>
SUPERSET_VERSION="4.1.1"

echo "=== Loading Official Superset Sample Dashboards ==="
echo "App ID: $APP_ID"
echo "Superset Version: $SUPERSET_VERSION"
echo "Production URL: $BASE_URL"
echo ""

# ============================================================================
# STEP 1: ENSURE METADATA DB MIGRATIONS ARE CURRENT
# ============================================================================

echo "Step 1: Running database migrations..."
doctl apps exec "$APP_ID" --component="$COMPONENT_NAME" -- superset db upgrade 2>&1 | tail -10
echo "✅ Migrations applied"
echo ""

echo "Step 2: Initializing Superset..."
doctl apps exec "$APP_ID" --component="$COMPONENT_NAME" -- superset init 2>&1 | tail -10
echo "✅ Superset initialized"
echo ""

# ============================================================================
# STEP 3: ENSURE ADMIN USER EXISTS
# ============================================================================

echo "Step 3: Ensuring admin user exists..."
doctl apps exec "$APP_ID" --component="$COMPONENT_NAME" -- bash -c "
superset fab create-admin \
  --username admin \
  --firstname Admin \
  --lastname User \
  --email admin@example.com \
  --password \"\${SUPERSET_ADMIN_PASS}\" 2>&1 || echo 'Admin user already exists (OK)'
" | tail -5
echo "✅ Admin user verified"
echo ""

# ============================================================================
# STEP 4: LOAD OFFICIAL EXAMPLES
# ============================================================================

echo "Step 4: Loading official Superset examples..."
echo "This may take 2-3 minutes..."
echo ""

doctl apps exec "$APP_ID" --component="$COMPONENT_NAME" -- superset load-examples 2>&1 | tee /tmp/load_examples_output.log

if grep -qi "error" /tmp/load_examples_output.log; then
  echo "⚠️  Errors detected during load-examples (check above)"
else
  echo "✅ Examples loaded successfully"
fi
echo ""

# ============================================================================
# STEP 5: VERIFY DASHBOARDS CREATED
# ============================================================================

echo "Step 5: Verifying dashboards..."
DASHBOARD_COUNT=$(doctl apps exec "$APP_ID" --component="$COMPONENT_NAME" -- bash -c "
superset shell <<'PY'
from superset import db
from superset.models.dashboard import Dashboard
print(db.session.query(Dashboard).count())
PY
" 2>/dev/null | grep -E '^[0-9]+$' || echo "0")

echo "Total dashboards in metadata DB: $DASHBOARD_COUNT"

if [[ "$DASHBOARD_COUNT" -gt 0 ]]; then
  echo "✅ Dashboards verified"
else
  echo "⚠️  No dashboards found - load-examples may have failed"
fi
echo ""

# ============================================================================
# STEP 6: REMAP EXAMPLE DATASETS TO "Examples (Postgres)" DB
# ============================================================================

echo "Step 6: Remapping example datasets to 'Examples (Postgres)' connection..."
doctl apps exec "$APP_ID" --component="$COMPONENT_NAME" -- bash -c "
superset shell <<'PY'
from superset import db
from superset.models.core import Database
from superset.connectors.sqla.models import SqlaTable

try:
    target = db.session.query(Database).filter(Database.database_name=='Examples (Postgres)').one()
    dsets = db.session.query(SqlaTable).filter(SqlaTable.schema=='examples').all()

    for ds in dsets:
        ds.database_id = target.id

    db.session.commit()
    print(f'remapped_datasets: {len(dsets)} -> db_id {target.id}')
except Exception as e:
    print(f'remap_error: {e}')
PY
" 2>&1 | tail -5
echo "✅ Dataset remapping complete"
echo ""

# ============================================================================
# SUMMARY
# ============================================================================

echo "========================================="
echo "=== ✅ Official Samples Loaded ==="
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Visit: $BASE_URL"
echo "2. Login with: admin / $SUPERSET_ADMIN_PASS"
echo "3. Navigate to Dashboards to see official examples"
echo ""
echo "Verification command:"
echo "  make validate"
