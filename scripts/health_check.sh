#!/bin/bash
# health_check.sh - Check health of all PPM components
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "==================================="
echo " PPM System Health Check"
echo "==================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

OVERALL_STATUS=0

# Check function
check() {
    local name=$1
    local command=$2

    echo -n "  Checking $name... "
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
        return 0
    else
        echo -e "${RED}FAILED${NC}"
        OVERALL_STATUS=1
        return 1
    fi
}

# Check with output
check_with_output() {
    local name=$1
    local command=$2

    echo -n "  Checking $name... "
    local output
    if output=$(eval "$command" 2>&1); then
        echo -e "${GREEN}OK${NC}"
        echo "    $output"
        return 0
    else
        echo -e "${RED}FAILED${NC}"
        echo "    $output"
        OVERALL_STATUS=1
        return 1
    fi
}

# 1. Check Control Room API
echo -e "\n${YELLOW}1. Control Room API${NC}"

CONTROL_ROOM_URL="${CONTROL_ROOM_URL:-http://localhost:3000}"

check "API reachable" "curl -s -o /dev/null -w '%{http_code}' '$CONTROL_ROOM_URL/api/health' | grep -q '200\\|503'"

if [ -n "$CONTROL_ROOM_URL" ]; then
    HEALTH_RESPONSE=$(curl -s "$CONTROL_ROOM_URL/api/health" 2>/dev/null || echo '{"status":"error"}')
    API_STATUS=$(echo "$HEALTH_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('status','unknown'))" 2>/dev/null || echo "error")

    if [ "$API_STATUS" == "healthy" ]; then
        echo -e "  Health status: ${GREEN}$API_STATUS${NC}"
    elif [ "$API_STATUS" == "degraded" ]; then
        echo -e "  Health status: ${YELLOW}$API_STATUS${NC}"
        OVERALL_STATUS=1
    else
        echo -e "  Health status: ${RED}$API_STATUS${NC}"
        OVERALL_STATUS=1
    fi
fi

# 2. Check Databricks connectivity
echo -e "\n${YELLOW}2. Databricks${NC}"

if [ -n "$DATABRICKS_HOST" ] && [ -n "$DATABRICKS_TOKEN" ]; then
    check "Workspace reachable" "curl -s -o /dev/null -w '%{http_code}' -H 'Authorization: Bearer $DATABRICKS_TOKEN' '$DATABRICKS_HOST/api/2.0/clusters/list' | grep -q '200'"

    # Check job status
    if command -v databricks &> /dev/null; then
        echo "  Checking jobs..."
        # This would require databricks CLI to be configured
        echo "    (Run 'databricks jobs list' for detailed status)"
    fi
else
    echo -e "  ${YELLOW}Skipped: DATABRICKS_HOST/TOKEN not set${NC}"
fi

# 3. Check data freshness
echo -e "\n${YELLOW}3. Data Freshness${NC}"

if [ -n "$DATABRICKS_HOST" ] && [ -n "$DATABRICKS_TOKEN" ]; then
    echo "  (Requires Databricks SQL access to check table freshness)"
    echo "  Run: SELECT MAX(synced_at) FROM bronze.notion_raw_pages"
else
    echo -e "  ${YELLOW}Skipped: Databricks not configured${NC}"
fi

# 4. Check Notion API
echo -e "\n${YELLOW}4. Notion API${NC}"

if [ -n "$NOTION_API_KEY" ]; then
    check "API accessible" "curl -s -o /dev/null -w '%{http_code}' -H 'Authorization: Bearer $NOTION_API_KEY' -H 'Notion-Version: 2022-06-28' 'https://api.notion.com/v1/users/me' | grep -q '200'"
else
    echo -e "  ${YELLOW}Skipped: NOTION_API_KEY not set${NC}"
fi

# 5. Check Azure (optional)
echo -e "\n${YELLOW}5. Azure Advisor${NC}"

if [ -n "$AZURE_TENANT_ID" ] && [ -n "$AZURE_CLIENT_ID" ]; then
    echo "  (Azure Resource Graph check requires Azure CLI)"
    echo "  Run: az graph query -q 'AdvisorResources | limit 1'"
else
    echo -e "  ${YELLOW}Skipped: Azure credentials not set${NC}"
fi

# Summary
echo ""
echo "==================================="
if [ $OVERALL_STATUS -eq 0 ]; then
    echo -e " ${GREEN}All checks passed!${NC}"
else
    echo -e " ${RED}Some checks failed${NC}"
fi
echo "==================================="

exit $OVERALL_STATUS
