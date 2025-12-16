#!/usr/bin/env bash
set -euo pipefail

# Get Apache Superset Image Digest (linux/amd64)
#
# Retrieves the SHA256 digest for a specific Superset version tag.
# IMPORTANT: Selects linux/amd64 platform digest for DO App Platform compatibility.
#
# Usage: ./scripts/get_image_digest.sh [VERSION]
#
# Examples:
#   ./scripts/get_image_digest.sh 4.1.1
#   ./scripts/get_image_digest.sh latest  # not recommended for production

VERSION="${1:-4.1.1}"
IMAGE="apache/superset:$VERSION"
PLATFORM="linux/amd64"

echo "=== Getting Image Digest (linux/amd64) ==="
echo "Image: $IMAGE"
echo "Platform: $PLATFORM"
echo ""

# ============================================================================
# METHOD 1: Docker buildx imagetools (most reliable for multi-arch)
# ============================================================================

if command -v docker &>/dev/null && docker buildx version &>/dev/null 2>&1; then
    echo "Method 1: Using docker buildx imagetools..."

    # Get manifest info and extract linux/amd64 digest
    INSPECT_OUTPUT=$(docker buildx imagetools inspect "$IMAGE" 2>&1 || true)

    if [[ -n "$INSPECT_OUTPUT" ]] && [[ "$INSPECT_OUTPUT" != *"error"* ]]; then
        # Parse the linux/amd64 digest from imagetools output
        # Format: Platform: linux/amd64 followed by Digest: sha256:...
        AMD64_DIGEST=$(echo "$INSPECT_OUTPUT" | awk '
            /Platform:.*linux\/amd64/ { found=1 }
            found && /Digest:/ { print $2; exit }
        ')

        if [[ -n "$AMD64_DIGEST" ]]; then
            echo ""
            echo "✅ linux/amd64 digest:"
            echo "   $AMD64_DIGEST"
            echo ""
            echo "For DO App Platform spec (infra/do/superset-app.yaml):"
            echo ""
            echo "  image:"
            echo "    registry_type: DOCKER_HUB"
            echo "    registry: apache"
            echo "    repository: superset"
            echo "    digest: $AMD64_DIGEST"
            echo ""
            echo "Deploy command:"
            echo "  doctl apps update \$APP_ID --spec infra/do/superset-app.yaml --update-sources"
            echo ""
            exit 0
        fi
    fi
    echo "   ⚠️  Docker buildx method failed, trying alternatives..."
    echo ""
fi

# ============================================================================
# METHOD 2: Docker Hub Registry API (no Docker required)
# ============================================================================

echo "Method 2: Using Docker Hub Registry API..."

# Get auth token for Docker Hub
TOKEN=$(curl -sS "https://auth.docker.io/token?service=registry.docker.io&scope=repository:apache/superset:pull" \
    | python3 -c 'import sys,json; print(json.load(sys.stdin).get("token",""))' 2>/dev/null || echo "")

if [[ -z "$TOKEN" ]]; then
    echo "❌ Failed to get Docker Hub token" >&2
    exit 1
fi

# Get fat manifest (manifest list) - this contains all platform variants
FAT_MANIFEST=$(curl -sS \
    -H "Authorization: Bearer $TOKEN" \
    -H "Accept: application/vnd.docker.distribution.manifest.list.v2+json,application/vnd.oci.image.index.v1+json" \
    "https://registry-1.docker.io/v2/apache/superset/manifests/$VERSION" 2>&1 || true)

# Check if this is a multi-arch manifest list
if echo "$FAT_MANIFEST" | python3 -c 'import sys,json; d=json.load(sys.stdin); exit(0 if d.get("manifests") else 1)' 2>/dev/null; then
    echo "   Multi-arch image detected, selecting linux/amd64..."

    # Extract linux/amd64 digest from manifest list
    AMD64_DIGEST=$(echo "$FAT_MANIFEST" | python3 -c '
import sys, json
data = json.load(sys.stdin)
for m in data.get("manifests", []):
    p = m.get("platform", {})
    if p.get("os") == "linux" and p.get("architecture") == "amd64":
        print(m.get("digest", ""))
        break
' 2>/dev/null || echo "")

    if [[ -n "$AMD64_DIGEST" ]]; then
        echo ""
        echo "✅ linux/amd64 digest:"
        echo "   $AMD64_DIGEST"
        echo ""
        echo "For DO App Platform spec (infra/do/superset-app.yaml):"
        echo ""
        echo "  image:"
        echo "    registry_type: DOCKER_HUB"
        echo "    registry: apache"
        echo "    repository: superset"
        echo "    digest: $AMD64_DIGEST"
        echo ""
        echo "Deploy command:"
        echo "  doctl apps update \$APP_ID --spec infra/do/superset-app.yaml --update-sources"
        echo ""
        exit 0
    else
        echo "❌ Could not find linux/amd64 in manifest list" >&2
        echo "Available platforms:" >&2
        echo "$FAT_MANIFEST" | python3 -c '
import sys, json
data = json.load(sys.stdin)
for m in data.get("manifests", []):
    p = m.get("platform", {})
    print(f"  - {p.get(\"os\")}/{p.get(\"architecture\")}")
' 2>/dev/null || true
        exit 1
    fi
else
    # Single-arch image - get digest from header
    echo "   Single-arch image, getting digest from headers..."

    MANIFEST_RESP=$(curl -sS -I \
        -H "Authorization: Bearer $TOKEN" \
        -H "Accept: application/vnd.docker.distribution.manifest.v2+json" \
        "https://registry-1.docker.io/v2/apache/superset/manifests/$VERSION" 2>&1 || true)

    DIGEST=$(echo "$MANIFEST_RESP" | grep -i "docker-content-digest:" | awk '{print $2}' | tr -d '\r')

    if [[ -n "$DIGEST" ]]; then
        echo ""
        echo "✅ Image digest:"
        echo "   $DIGEST"
        echo ""
        echo "For DO App Platform spec (infra/do/superset-app.yaml):"
        echo ""
        echo "  image:"
        echo "    registry_type: DOCKER_HUB"
        echo "    registry: apache"
        echo "    repository: superset"
        echo "    digest: $DIGEST"
        echo ""
        echo "Deploy command:"
        echo "  doctl apps update \$APP_ID --spec infra/do/superset-app.yaml --update-sources"
        echo ""
        exit 0
    else
        echo "❌ Failed to get digest for $IMAGE" >&2
        echo "Response headers:" >&2
        echo "$MANIFEST_RESP" | head -20 >&2
        exit 1
    fi
fi

# ============================================================================
# METHOD 3: From running DO deployment (reference only)
# ============================================================================

echo "---"
echo ""
echo "Alternative: Get digest from running DO deployment:"
echo ""
echo "  APP_ID=\"73af11cb-dab2-4cb1-9770-291c536531e6\""
echo "  doctl apps get \$APP_ID --output json | jq '.spec.services[].image'"
echo ""
