#!/bin/bash
# deploy_scout_views.sh
# Deploys Scout Dashboard views to PostgreSQL database
#
# Usage: ./deploy_scout_views.sh
#
# Requires: EXAMPLES_DB_URI environment variable

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== Scout Dashboard Views Deployment ==="
echo ""

# Validate environment
if [[ -z "${EXAMPLES_DB_URI:-}" ]]; then
    echo "BLOCKED: missing env var EXAMPLES_DB_URI"
    exit 1
fi

echo "Target database: [redacted]"
echo ""

# Option 1: Deploy consolidated migration
echo "Deploying Scout Dashboard views..."
psql "${EXAMPLES_DB_URI}" -f "${SCRIPT_DIR}/V001__create_scout_dashboard_views.sql"

# Verify deployment
echo ""
echo "=== Verifying Deployment ==="

psql "${EXAMPLES_DB_URI}" -c "
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_schema = 'public'
AND (table_name LIKE 'dim_%' OR table_name LIKE 'bi_%')
ORDER BY table_name;
"

echo ""
echo "=== View Row Counts ==="

psql "${EXAMPLES_DB_URI}" -c "
SELECT 'dim_client' AS view_name, COUNT(*) AS row_count FROM dim_client
UNION ALL SELECT 'dim_brand', COUNT(*) FROM dim_brand
UNION ALL SELECT 'dim_campaign', COUNT(*) FROM dim_campaign
UNION ALL SELECT 'dim_channel', COUNT(*) FROM dim_channel
UNION ALL SELECT 'dim_market', COUNT(*) FROM dim_market
UNION ALL SELECT 'dim_time', COUNT(*) FROM dim_time
UNION ALL SELECT 'bi_fact_campaign_performance', COUNT(*) FROM bi_fact_campaign_performance
UNION ALL SELECT 'bi_campaign_summary', COUNT(*) FROM bi_campaign_summary
ORDER BY view_name;
"

echo ""
echo "=== Deployment Complete ==="
