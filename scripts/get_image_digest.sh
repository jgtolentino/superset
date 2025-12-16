#!/usr/bin/env bash
set -euo pipefail

# Get Apache Superset Image Digest
#
# Retrieves the SHA256 digest for a specific Superset version tag.
# Use this digest in DO App Platform spec for reproducible deployments.
#
# Usage: ./scripts/get_image_digest.sh [VERSION]
#
# Examples:
#   ./scripts/get_image_digest.sh 4.1.1
#   ./scripts/get_image_digest.sh latest  # not recommended for production

VERSION="${1:-4.1.1}"
IMAGE="apache/superset:$VERSION"

echo "=== Getting Image Digest ==="
echo "Image: $IMAGE"
echo ""

# ============================================================================
# METHOD 1: Docker (if available and image is pulled)
# ============================================================================

if command -v docker &>/dev/null; then
    echo "Method 1: Using Docker..."

    # Pull the image to ensure we have the latest digest
    echo "   Pulling $IMAGE..."
    if docker pull "$IMAGE" 2>&1 | tail -3; then
        DIGEST=$(docker inspect --format='{{index .RepoDigests 0}}' "$IMAGE" 2>/dev/null || echo "")

        if [[ -n "$DIGEST" ]]; then
            echo ""
            echo "✅ Image digest:"
            echo "   $DIGEST"
            echo ""
            echo "For DO App Platform spec (infra/do/superset-app.yaml):"
            echo ""
            echo "  image:"
            echo "    registry_type: DOCKER_HUB"
            echo "    repository: apache/superset"
            # Extract just the sha256:... part
            SHA=$(echo "$DIGEST" | sed 's/.*@//')
            echo "    digest: $SHA"
            echo ""
            exit 0
        fi
    fi
    echo "   ⚠️  Docker method failed, trying alternatives..."
    echo ""
fi

# ============================================================================
# METHOD 2: Docker Hub API (no Docker required)
# ============================================================================

echo "Method 2: Using Docker Hub API..."

# Get token for Docker Hub
TOKEN=$(curl -sS "https://auth.docker.io/token?service=registry.docker.io&scope=repository:apache/superset:pull" \
    | python3 -c 'import sys,json; print(json.load(sys.stdin).get("token",""))' 2>/dev/null || echo "")

if [[ -z "$TOKEN" ]]; then
    echo "❌ Failed to get Docker Hub token" >&2
    exit 1
fi

# Get manifest (with digest header)
MANIFEST_RESP=$(curl -sS -I \
    -H "Authorization: Bearer $TOKEN" \
    -H "Accept: application/vnd.docker.distribution.manifest.v2+json" \
    "https://registry-1.docker.io/v2/apache/superset/manifests/$VERSION" 2>&1 || true)

DIGEST=$(echo "$MANIFEST_RESP" | grep -i "docker-content-digest:" | awk '{print $2}' | tr -d '\r')

if [[ -n "$DIGEST" ]]; then
    echo ""
    echo "✅ Image digest:"
    echo "   apache/superset@$DIGEST"
    echo ""
    echo "For DO App Platform spec (infra/do/superset-app.yaml):"
    echo ""
    echo "  image:"
    echo "    registry_type: DOCKER_HUB"
    echo "    repository: apache/superset"
    echo "    digest: $DIGEST"
    echo ""
else
    echo "❌ Failed to get digest for $IMAGE" >&2
    echo "Response headers:" >&2
    echo "$MANIFEST_RESP" | head -20 >&2
    exit 1
fi

# ============================================================================
# METHOD 3: From running DO deployment
# ============================================================================

echo "---"
echo ""
echo "Alternative: Get digest from running DO deployment:"
echo ""
echo "  APP_ID=\"73af11cb-dab2-4cb1-9770-291c536531e6\""
echo "  doctl apps get \$APP_ID --output json | jq '.spec.services[].image'"
echo ""
