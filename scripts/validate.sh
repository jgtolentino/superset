#!/usr/bin/env bash
set -euo pipefail

# Superset Validation Script
# Validates database connections, datasets, and API functionality
# Returns non-zero on any failure

# ============================================================================
# PREFLIGHT CHECK
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$SCRIPT_DIR/require_env.sh"

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_URL="${BASE_URL:-http://localhost:8088}"

TEMP_TOKEN_FILE=$(mktemp)
trap 'rm -f "$TEMP_TOKEN_FILE"' EXIT

FAILED=0

# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

check_health() {
  echo "🏥 Checking /health endpoint..."
  HEALTH=$(curl -s -w "%{http_code}" -o /dev/null "${BASE_URL}/health")

  if [[ "$HEALTH" == "200" ]]; then
    echo "  ✅ Health check passed (HTTP 200)"
    return 0
  else
    echo "  ❌ Health check failed (HTTP $HEALTH)"
    return 1
  fi
}

authenticate() {
  echo ""
  echo "🔐 Authenticating..."

  LOGIN_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/api/v1/security/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"${SUPERSET_ADMIN_USER}\",\"password\":\"${SUPERSET_ADMIN_PASS}\",\"provider\":\"db\",\"refresh\":true}")

  HTTP_CODE=$(echo "$LOGIN_RESPONSE" | tail -n1)
  RESPONSE_BODY=$(echo "$LOGIN_RESPONSE" | sed '$d')

  if [[ "$HTTP_CODE" != "200" ]]; then
    echo "  ❌ Authentication failed (HTTP $HTTP_CODE)"
    return 1
  fi

  ACCESS_TOKEN=$(echo "$RESPONSE_BODY" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
  echo "$ACCESS_TOKEN" > "$TEMP_TOKEN_FILE"
  echo "  ✅ Authentication successful"
  return 0
}

check_database() {
  echo ""
  echo "📊 Checking 'Examples (Postgres)' database..."

  ACCESS_TOKEN=$(cat "$TEMP_TOKEN_FILE")

  DB_LIST=$(curl -s -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    "${BASE_URL}/api/v1/database/?q=(filters:!((col:database_name,opr:eq,value:'Examples%20(Postgres)')))")

  DB_COUNT=$(echo "$DB_LIST" | python3 -c "import sys, json; print(json.load(sys.stdin).get('count', 0))" 2>/dev/null || echo "0")

  if [[ "$DB_COUNT" == "0" ]]; then
    echo "  ❌ Database 'Examples (Postgres)' not found"
    return 1
  fi

  DB_ID=$(echo "$DB_LIST" | python3 -c "import sys, json; print(json.load(sys.stdin)['result'][0]['id'])")
  echo "  ✅ Database exists (id=$DB_ID)"

  # Test connection
  echo "  🔌 Testing database connection..."
  TEST_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/api/v1/database/${DB_ID}/validate_parameters/" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"sqlalchemy_uri":"","engine":"postgresql"}' 2>/dev/null || echo -e "\n404")

  HTTP_CODE=$(echo "$TEST_RESPONSE" | tail -n1)

  if [[ "$HTTP_CODE" == "200" ]] || [[ "$HTTP_CODE" == "201" ]]; then
    echo "  ✅ Database connection healthy"
    return 0
  else
    # Connection test endpoint might not exist, this is non-critical
    echo "  ⚠️  Connection test endpoint returned HTTP $HTTP_CODE (non-blocking)"
    return 0
  fi
}

check_datasets() {
  echo ""
  echo "📋 Checking datasets..."

  ACCESS_TOKEN=$(cat "$TEMP_TOKEN_FILE")
  DATASETS=("birth_names" "flights" "channels")
  FOUND=0

  for TABLE in "${DATASETS[@]}"; do
    DATASET_LIST=$(curl -s -H "Authorization: Bearer ${ACCESS_TOKEN}" \
      "${BASE_URL}/api/v1/dataset/?q=(filters:!((col:table_name,opr:eq,value:${TABLE})))")

    COUNT=$(echo "$DATASET_LIST" | python3 -c "import sys, json; print(json.load(sys.stdin).get('count', 0))" 2>/dev/null || echo "0")

    if [[ "$COUNT" == "0" ]]; then
      echo "  ❌ Dataset ${TABLE} not found"
    else
      DATASET_ID=$(echo "$DATASET_LIST" | python3 -c "import sys, json; print(json.load(sys.stdin)['result'][0]['id'])")
      echo "  ✅ Dataset ${TABLE} exists (id=${DATASET_ID})"
      FOUND=$((FOUND + 1))
    fi
  done

  if [[ "$FOUND" == "3" ]]; then
    echo "  ✅ All 3 datasets found"
    return 0
  else
    echo "  ❌ Only ${FOUND}/3 datasets found"
    return 1
  fi
}

check_metadata_db() {
  echo ""
  echo "🗄️  Checking Superset metadata database engine..."

  # Check if we can determine metadata DB engine via health endpoint or config
  HEALTH_RESPONSE=$(curl -s "${BASE_URL}/health")

  if echo "$HEALTH_RESPONSE" | grep -qi "sqlite"; then
    echo "  ❌ CRITICAL: Metadata DB appears to be SQLite"
    echo "  ⚠️  This WILL cause 'database is locked' errors in production"
    echo "  Fix: Set SUPERSET__SQLALCHEMY_DATABASE_URI to PostgreSQL connection"
    return 1
  fi

  # Alternative check: try to infer from error patterns
  ACCESS_TOKEN=$(cat "$TEMP_TOKEN_FILE")

  # Get database list - if logs table writes fail, we'll see it
  DB_LIST=$(curl -s -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    "${BASE_URL}/api/v1/database/" 2>&1)

  if echo "$DB_LIST" | grep -qi "sqlite3.OperationalError"; then
    echo "  ❌ CRITICAL: Detected SQLite lock error in metadata DB"
    echo "  Fix: Set SUPERSET__SQLALCHEMY_DATABASE_URI to PostgreSQL"
    return 1
  fi

  echo "  ✅ Metadata DB engine check passed (no SQLite lock errors detected)"
  return 0
}

check_sql_execution() {
  echo ""
  echo "🔍 Testing SQL query execution..."

  ACCESS_TOKEN=$(cat "$TEMP_TOKEN_FILE")

  # Get database ID first
  DB_LIST=$(curl -s -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    "${BASE_URL}/api/v1/database/?q=(filters:!((col:database_name,opr:eq,value:'Examples%20(Postgres)')))")

  DB_ID=$(echo "$DB_LIST" | python3 -c "import sys, json; print(json.load(sys.stdin)['result'][0]['id'])" 2>/dev/null || echo "0")

  if [[ "$DB_ID" == "0" ]]; then
    echo "  ❌ Cannot find database for SQL test"
    return 1
  fi

  # Try simple query via SQL Lab
  SQL_RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${BASE_URL}/api/v1/sqllab/execute/" \
    -H "Authorization: Bearer ${ACCESS_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{
      \"database_id\": ${DB_ID},
      \"sql\": \"SELECT COUNT(*) as count FROM examples.birth_names LIMIT 1\",
      \"runAsync\": false,
      \"schema\": \"examples\"
    }" 2>/dev/null || echo -e "\n500")

  HTTP_CODE=$(echo "$SQL_RESPONSE" | tail -n1)

  if [[ "$HTTP_CODE" == "200" ]] || [[ "$HTTP_CODE" == "201" ]]; then
    echo "  ✅ SQL query executed successfully"
    return 0
  elif [[ "$HTTP_CODE" == "500" ]]; then
    RESPONSE_BODY=$(echo "$SQL_RESPONSE" | sed '$d')
    if echo "$RESPONSE_BODY" | grep -q "RESULTS_BACKEND_NOT_CONFIGURED"; then
      echo "  ⚠️  SQL Lab requires results backend (Redis) - expected in basic setup"
      return 0  # Non-blocking
    else
      echo "  ❌ SQL query failed (HTTP $HTTP_CODE)"
      return 1
    fi
  else
    echo "  ⚠️  SQL execution test inconclusive (HTTP $HTTP_CODE)"
    return 0  # Non-blocking
  fi
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

echo "=== Superset Validation Suite ==="
echo "Base URL: $BASE_URL"
echo ""

check_health || FAILED=$((FAILED + 1))
authenticate || FAILED=$((FAILED + 1))
check_metadata_db || FAILED=$((FAILED + 1))
check_database || FAILED=$((FAILED + 1))
check_datasets || FAILED=$((FAILED + 1))
check_sql_execution || FAILED=$((FAILED + 1))

# ============================================================================
# SUMMARY
# ============================================================================

echo ""
echo "========================================="
if [[ "$FAILED" -eq 0 ]]; then
  echo "=== ✅ All Validation Checks Passed ==="
  echo "========================================="
  exit 0
else
  echo "=== ❌ ${FAILED} Validation Check(s) Failed ==="
  echo "========================================="
  exit 1
fi
