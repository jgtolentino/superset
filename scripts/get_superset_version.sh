#!/usr/bin/env bash
set -euo pipefail

# Get Superset Version via Authenticated API
#
# This script gets the actual running Superset version using the authenticated
# /api/v1/version endpoint, which may require authentication on some deployments.
#
# Usage: ./scripts/get_superset_version.sh [BASE_URL]
#
# Environment variables:
#   BASE_URL           - Superset instance URL (or pass as argument)
#   SUPERSET_ADMIN_USER - Admin username
#   SUPERSET_ADMIN_PASS - Admin password

# ============================================================================
# CONFIGURATION
# ============================================================================

BASE_URL="${1:-${BASE_URL:-}}"

if [[ -z "$BASE_URL" ]]; then
    echo "Usage: $0 <BASE_URL>" >&2
    echo "  or: export BASE_URL=https://superset.example.com && $0" >&2
    exit 1
fi

# Remove trailing slash if present
BASE_URL="${BASE_URL%/}"

echo "=== Superset Version Check ==="
echo "Instance: $BASE_URL"
echo ""

# ============================================================================
# STEP 1: Try unauthenticated version endpoint first
# ============================================================================

echo "Step 1: Trying unauthenticated /api/v1/version..."
# Use -L to follow redirects (e.g., / -> /superset/welcome/)
UNAUTH_RESPONSE=$(curl -sSL -w "\n%{http_code}" "$BASE_URL/api/v1/version" 2>&1 || true)
HTTP_CODE=$(echo "$UNAUTH_RESPONSE" | tail -1)
BODY=$(echo "$UNAUTH_RESPONSE" | head -n -1)

if [[ "$HTTP_CODE" == "200" ]] && [[ -n "$BODY" ]] && [[ "$BODY" != *"<!DOCTYPE"* ]]; then
    echo "✅ Version endpoint accessible without auth:"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"
    exit 0
fi

echo "   HTTP $HTTP_CODE - Authentication required"
echo ""

# ============================================================================
# STEP 2: Authenticate and get version
# ============================================================================

echo "Step 2: Authenticating..."

if [[ -z "${SUPERSET_ADMIN_USER:-}" ]] || [[ -z "${SUPERSET_ADMIN_PASS:-}" ]]; then
    echo "❌ BLOCKED: SUPERSET_ADMIN_USER and SUPERSET_ADMIN_PASS required for authenticated access" >&2
    echo "" >&2
    echo "Set credentials:" >&2
    echo "  export SUPERSET_ADMIN_USER='your_username'" >&2
    echo "  export SUPERSET_ADMIN_PASS='your_password'" >&2
    exit 2
fi

# Get access token (use -L to follow any redirects)
LOGIN_RESPONSE=$(curl -sSL "$BASE_URL/api/v1/security/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$SUPERSET_ADMIN_USER\",\"password\":\"$SUPERSET_ADMIN_PASS\",\"provider\":\"db\"}" 2>&1)

ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("access_token",""))' 2>/dev/null || echo "")

if [[ -z "$ACCESS_TOKEN" ]]; then
    echo "❌ Authentication failed" >&2
    echo "Response: $LOGIN_RESPONSE" >&2
    exit 3
fi

echo "   ✅ Authenticated successfully"
echo ""

# ============================================================================
# STEP 3: Get version with authentication
# ============================================================================

echo "Step 3: Getting version (authenticated)..."

VERSION_RESPONSE=$(curl -sSL -w "\n%{http_code}" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    "$BASE_URL/api/v1/version" 2>&1)

HTTP_CODE=$(echo "$VERSION_RESPONSE" | tail -1)
BODY=$(echo "$VERSION_RESPONSE" | head -n -1)

if [[ "$HTTP_CODE" == "200" ]]; then
    echo "✅ Version info:"
    echo "$BODY" | python3 -m json.tool 2>/dev/null || echo "$BODY"

    # Extract version for CI/scripting
    VERSION=$(echo "$BODY" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("result",{}).get("version","unknown"))' 2>/dev/null || echo "unknown")
    echo ""
    echo "SUPERSET_VERSION=$VERSION"
else
    echo "⚠️  HTTP $HTTP_CODE response:"
    echo "$BODY" | head -c 500
    echo ""

    # Try alternative endpoints
    echo ""
    echo "Step 4: Trying alternative info endpoints..."

    for endpoint in "/api/v1/me" "/api/v1/database/" "/health"; do
        RESP=$(curl -sSL -o /dev/null -w "%{http_code}" \
            -H "Authorization: Bearer $ACCESS_TOKEN" \
            "$BASE_URL$endpoint" 2>&1 || echo "000")
        echo "   $endpoint -> HTTP $RESP"
    done
fi

echo ""
echo "=== Done ==="
