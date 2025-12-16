#!/usr/bin/env bash
set -euo pipefail

# Superset Examples Database Bootstrap Script
# Creates/updates "Examples (Postgres)" database connection and datasets
# IDEMPOTENT: Safe to run multiple times

# ============================================================================
# PREFLIGHT CHECK
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$SCRIPT_DIR/require_env.sh"

BASE_URL="${BASE_URL:-http://localhost:8088}"

echo "=== Superset Examples Bootstrap ==="
echo "Base URL: $BASE_URL"
echo "DB URI: ${EXAMPLES_DB_URI:0:30}..." # Only show prefix

# ============================================================================
# AUTHENTICATION
# ============================================================================

echo ""
echo "🔐 Authenticating to Superset..."

LOGIN_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/api/v1/security/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"${SUPERSET_ADMIN_USER}\",\"password\":\"${SUPERSET_ADMIN_PASS}\",\"provider\":\"db\",\"refresh\":true}")

HTTP_CODE=$(echo "$LOGIN_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$LOGIN_RESPONSE" | sed '$d')

if [ "$HTTP_CODE" != "200" ]; then
  echo "❌ Authentication failed (HTTP $HTTP_CODE)"
  echo "$RESPONSE_BODY" | head -5
  exit 1
fi

ACCESS_TOKEN=$(echo "$RESPONSE_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
echo "✅ Authenticated successfully"

# ============================================================================
# CREATE/UPDATE DATABASE CONNECTION
# ============================================================================

echo ""
echo "📊 Creating/updating database: Examples (Postgres)"

# Check if database exists
DB_LIST=$(curl -s -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  "${BASE_URL}/api/v1/database/?q=(filters:!((col:database_name,opr:eq,value:'Examples%20(Postgres)')))")

DB_ID=$(echo "$DB_LIST" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('count', 0) > 0:
    print(data['result'][0]['id'])
else:
    print('0')
" 2>/dev/null || echo "0")

if [ "$DB_ID" = "0" ]; then
  echo "Creating new database connection..."

  CREATE_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/api/v1/database/" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{
      \"database_name\": \"Examples (Postgres)\",
      \"sqlalchemy_uri\": \"${EXAMPLES_DB_URI}\",
      \"expose_in_sqllab\": true,
      \"allow_ctas\": true,
      \"allow_cvas\": true,
      \"configuration_method\": \"sqlalchemy_form\"
    }")

  HTTP_CODE=$(echo "$CREATE_RESPONSE" | tail -n1)
  RESPONSE_BODY=$(echo "$CREATE_RESPONSE" | sed '$d')

  if [ "$HTTP_CODE" != "201" ]; then
    echo "❌ Failed to create database (HTTP $HTTP_CODE)"
    echo "$RESPONSE_BODY" | head -10
    exit 1
  fi

  DB_ID=$(echo "$RESPONSE_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
  echo "✅ Created database (id=$DB_ID)"
else
  echo "✅ Database already exists (id=$DB_ID)"
fi

# ============================================================================
# CREATE DATASETS
# ============================================================================

echo ""
echo "📋 Creating datasets..."

DATASETS=("birth_names" "flights" "channels")

for TABLE in "${DATASETS[@]}"; do
  echo "Processing dataset: $TABLE"

  # Check if dataset exists
  DATASET_LIST=$(curl -s -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    "${BASE_URL}/api/v1/dataset/?q=(filters:!((col:table_name,opr:eq,value:${TABLE})))")

  DATASET_COUNT=$(echo "$DATASET_LIST" | python3 -c "import sys, json; print(json.load(sys.stdin).get('count', 0))" 2>/dev/null || echo "0")

  if [ "$DATASET_COUNT" = "0" ]; then
    CREATE_DATASET=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/api/v1/dataset/" \
      -H "Authorization: Bearer ${ACCESS_TOKEN}" \
      -H "Content-Type: application/json" \
      -d "{
        \"database\": ${DB_ID},
        \"schema\": \"examples\",
        \"table_name\": \"${TABLE}\"
      }")

    HTTP_CODE=$(echo "$CREATE_DATASET" | tail -n1)

    if [ "$HTTP_CODE" = "201" ]; then
      DATASET_ID=$(echo "$CREATE_DATASET" | sed '$d' | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
      echo "  ✅ Created dataset ${TABLE} (id=${DATASET_ID})"
    else
      echo "  ⚠️  Failed to create dataset ${TABLE} (HTTP $HTTP_CODE)"
      echo "$CREATE_DATASET" | sed '$d' | head -5
    fi
  else
    echo "  ✅ Dataset ${TABLE} already exists"
  fi
done

# ============================================================================
# SUMMARY
# ============================================================================

echo ""
echo "=== ✅ Bootstrap Complete ==="
echo "Database ID: $DB_ID"
echo "Datasets: ${DATASETS[*]}"
echo ""
echo "Next: Run scripts/validate.sh to verify setup"
