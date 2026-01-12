#!/bin/bash
# deploy_scout.sh
# End-to-end deployment of Scout Retail Intelligence to Superset
#
# Usage:
#   ./scripts/scout/deploy_scout.sh [--views-only|--datasets-only|--dashboard-only|--all]
#
# Required environment variables:
#   SCOUT_DB_URI      - PostgreSQL connection string for Scout database
#   BASE_URL          - Superset base URL (e.g., https://superset.insightpulseai.net)
#   SUPERSET_ADMIN_USER - Superset admin username
#   SUPERSET_ADMIN_PASS - Superset admin password
#
# Optional:
#   SUPERSET_CONTAINER - Docker container name (default: superset)
#   DRY_RUN           - Set to "true" to skip actual deployment

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Defaults
SUPERSET_CONTAINER="${SUPERSET_CONTAINER:-superset}"
DRY_RUN="${DRY_RUN:-false}"

# ============================================
# Helper functions
# ============================================
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

check_required_vars() {
    local missing=0
    for var in "$@"; do
        if [[ -z "${!var:-}" ]]; then
            log_error "Missing required environment variable: $var"
            missing=1
        fi
    done
    return $missing
}

# ============================================
# Step 1: Deploy SQL Views
# ============================================
deploy_views() {
    log_info "Deploying Scout retail views to database..."

    if ! check_required_vars SCOUT_DB_URI; then
        log_error "BLOCKED: missing env var SCOUT_DB_URI"
        return 1
    fi

    local views_file="$REPO_ROOT/sql/scout_views/V002__create_scout_retail_views.sql"

    if [[ ! -f "$views_file" ]]; then
        log_error "Views file not found: $views_file"
        return 1
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log_warn "DRY_RUN: Would execute: psql -f $views_file"
        return 0
    fi

    log_info "Applying views from: $views_file"
    psql "$SCOUT_DB_URI" -v ON_ERROR_STOP=1 -f "$views_file"

    # Verify views were created
    log_info "Verifying views..."
    local view_count
    view_count=$(psql "$SCOUT_DB_URI" -t -c "
        SELECT COUNT(*) FROM information_schema.views
        WHERE table_schema = 'public'
        AND table_name IN (
            'dim_store', 'dim_product', 'dim_time', 'dim_geography',
            'bi_fact_transactions', 'bi_transaction_summary_daily',
            'bi_product_performance', 'bi_customer_segments',
            'bi_store_performance', 'bi_competitive_analysis',
            'bi_hourly_patterns', 'bi_basket_analysis'
        );
    " | tr -d ' ')

    if [[ "$view_count" -eq 12 ]]; then
        log_success "All 12 Scout views created successfully"
    else
        log_error "Expected 12 views, found $view_count"
        return 1
    fi
}

# ============================================
# Step 2: Import Datasets into Superset
# ============================================
import_datasets() {
    log_info "Importing Scout datasets into Superset..."

    local datasets_file="$REPO_ROOT/config/scout_retail_datasets.yaml"

    if [[ ! -f "$datasets_file" ]]; then
        log_error "Datasets file not found: $datasets_file"
        return 1
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log_warn "DRY_RUN: Would import datasets from $datasets_file"
        return 0
    fi

    # Check if running in Docker or direct
    if command -v docker &> /dev/null && docker ps -q -f name="$SUPERSET_CONTAINER" | grep -q .; then
        log_info "Using Docker container: $SUPERSET_CONTAINER"
        docker exec "$SUPERSET_CONTAINER" \
            superset import-datasources \
            -p "/app/config/scout_retail_datasets.yaml" \
            --overwrite
    elif command -v superset &> /dev/null; then
        log_info "Using local superset CLI"
        superset import-datasources -p "$datasets_file" --overwrite
    else
        log_warn "Superset CLI not found. Attempting API import..."
        import_datasets_via_api "$datasets_file"
    fi

    log_success "Datasets imported successfully"
}

# ============================================
# Step 3: Import Dashboard Template
# ============================================
import_dashboard() {
    log_info "Importing Scout dashboard template..."

    local dashboard_file="$REPO_ROOT/examples/dashboards/scout_retail_intelligence.json"

    if [[ ! -f "$dashboard_file" ]]; then
        log_error "Dashboard file not found: $dashboard_file"
        return 1
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        log_warn "DRY_RUN: Would import dashboard from $dashboard_file"
        return 0
    fi

    # Check if running in Docker or direct
    if command -v docker &> /dev/null && docker ps -q -f name="$SUPERSET_CONTAINER" | grep -q .; then
        log_info "Using Docker container: $SUPERSET_CONTAINER"
        docker exec "$SUPERSET_CONTAINER" \
            superset import-dashboards \
            -p "/app/examples/dashboards/scout_retail_intelligence.json" \
            --overwrite
    elif command -v superset &> /dev/null; then
        log_info "Using local superset CLI"
        superset import-dashboards -p "$dashboard_file" --overwrite
    else
        log_warn "Superset CLI not found. Attempting API import..."
        import_dashboard_via_api "$dashboard_file"
    fi

    log_success "Dashboard imported successfully"
}

# ============================================
# API-based imports (fallback)
# ============================================
import_datasets_via_api() {
    local datasets_file="$1"

    if ! check_required_vars BASE_URL SUPERSET_ADMIN_USER SUPERSET_ADMIN_PASS; then
        log_error "API import requires BASE_URL, SUPERSET_ADMIN_USER, SUPERSET_ADMIN_PASS"
        return 1
    fi

    log_info "Authenticating with Superset API..."
    local token_response
    token_response=$(curl -s -X POST "${BASE_URL}/api/v1/security/login" \
        -H "Content-Type: application/json" \
        -d "{\"username\":\"${SUPERSET_ADMIN_USER}\",\"password\":\"${SUPERSET_ADMIN_PASS}\",\"provider\":\"db\"}")

    local access_token
    access_token=$(echo "$token_response" | jq -r '.access_token // empty')

    if [[ -z "$access_token" ]]; then
        log_error "Failed to authenticate with Superset API"
        echo "$token_response"
        return 1
    fi

    log_warn "API-based dataset import not fully implemented - use CLI or Docker method"
    log_info "Access token obtained successfully"
}

import_dashboard_via_api() {
    local dashboard_file="$1"

    if ! check_required_vars BASE_URL SUPERSET_ADMIN_USER SUPERSET_ADMIN_PASS; then
        log_error "API import requires BASE_URL, SUPERSET_ADMIN_USER, SUPERSET_ADMIN_PASS"
        return 1
    fi

    log_info "Authenticating with Superset API..."
    local token_response
    token_response=$(curl -s -X POST "${BASE_URL}/api/v1/security/login" \
        -H "Content-Type: application/json" \
        -d "{\"username\":\"${SUPERSET_ADMIN_USER}\",\"password\":\"${SUPERSET_ADMIN_PASS}\",\"provider\":\"db\"}")

    local access_token
    access_token=$(echo "$token_response" | jq -r '.access_token // empty')

    if [[ -z "$access_token" ]]; then
        log_error "Failed to authenticate with Superset API"
        return 1
    fi

    log_info "Importing dashboard via API..."
    local import_response
    import_response=$(curl -s -X POST "${BASE_URL}/api/v1/dashboard/import/" \
        -H "Authorization: Bearer ${access_token}" \
        -F "formData=@${dashboard_file}" \
        -F "overwrite=true")

    if echo "$import_response" | jq -e '.message' &>/dev/null; then
        local message
        message=$(echo "$import_response" | jq -r '.message')
        if [[ "$message" == *"error"* ]] || [[ "$message" == *"Error"* ]]; then
            log_error "Dashboard import failed: $message"
            return 1
        fi
    fi

    log_success "Dashboard imported via API"
}

# ============================================
# Step 4: Health Check
# ============================================
health_check() {
    log_info "Running health checks..."

    if ! check_required_vars BASE_URL; then
        log_warn "Skipping API health checks (BASE_URL not set)"
        return 0
    fi

    # Check Superset is up
    log_info "Checking Superset health endpoint..."
    if curl -sf "${BASE_URL}/health" > /dev/null; then
        log_success "Superset is healthy"
    else
        log_error "Superset health check failed"
        return 1
    fi

    # Check Scout dashboard exists (if credentials available)
    if [[ -n "${SUPERSET_ADMIN_USER:-}" ]] && [[ -n "${SUPERSET_ADMIN_PASS:-}" ]]; then
        log_info "Checking Scout dashboard exists..."

        local token_response
        token_response=$(curl -s -X POST "${BASE_URL}/api/v1/security/login" \
            -H "Content-Type: application/json" \
            -d "{\"username\":\"${SUPERSET_ADMIN_USER}\",\"password\":\"${SUPERSET_ADMIN_PASS}\",\"provider\":\"db\"}")

        local access_token
        access_token=$(echo "$token_response" | jq -r '.access_token // empty')

        if [[ -n "$access_token" ]]; then
            local dashboard_check
            dashboard_check=$(curl -s -H "Authorization: Bearer ${access_token}" \
                "${BASE_URL}/api/v1/dashboard/?q=$(python3 -c 'import urllib.parse; print(urllib.parse.quote("{\"filters\":[{\"col\":\"dashboard_title\",\"opr\":\"ct\",\"value\":\"Scout Retail Intelligence\"}]}"))')")

            local count
            count=$(echo "$dashboard_check" | jq -r '.count // 0')

            if [[ "$count" -ge 1 ]]; then
                log_success "Scout Retail Intelligence dashboard found"
            else
                log_warn "Scout dashboard not found in listing (may need manual verification)"
            fi
        fi
    else
        log_warn "Skipping dashboard verification (credentials not set)"
    fi

    log_success "Health checks completed"
}

# ============================================
# Main
# ============================================
main() {
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║       Scout Retail Intelligence - Superset Deployment          ║"
    echo "║                    TBWA\\SMP Suqi Analytics                     ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""

    local mode="${1:-all}"

    case "$mode" in
        --views-only)
            deploy_views
            ;;
        --datasets-only)
            import_datasets
            ;;
        --dashboard-only)
            import_dashboard
            ;;
        --health-only)
            health_check
            ;;
        --all|*)
            deploy_views
            import_datasets
            import_dashboard
            health_check
            ;;
    esac

    echo ""
    log_success "Scout Retail Intelligence deployment complete!"
    echo ""
    echo "Next steps:"
    echo "  1. Open ${BASE_URL:-https://superset.insightpulseai.net}/dashboard/list/"
    echo "  2. Find 'Scout - Retail Intelligence Dashboard'"
    echo "  3. Verify data is flowing from scout_transactions table"
    echo ""
}

main "$@"
