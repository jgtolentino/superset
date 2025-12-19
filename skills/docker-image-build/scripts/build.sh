#!/usr/bin/env bash
# Build multi-architecture Docker image using buildx
#
# Usage:
#   ./build.sh [--push] [--load]
#
# Environment variables:
#   IMAGE_REPO   - Image repository (default: ghcr.io/jgtolentino/ipai-superset)
#   IMAGE_TAG    - Image tag (default: latest)
#   PLATFORMS    - Target platforms (default: linux/amd64,linux/arm64)
#   DOCKERFILE   - Dockerfile path (default: Dockerfile)
#   BUILD_CONTEXT - Build context (default: .)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# =============================================================================
# PARSE ARGUMENTS
# =============================================================================

PUSH_FLAG=""
LOAD_FLAG=""
EXTRA_ARGS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --push)
            PUSH_FLAG="--push"
            shift
            ;;
        --load)
            LOAD_FLAG="--load"
            # Load only works with single platform
            PLATFORMS="linux/amd64"
            shift
            ;;
        *)
            EXTRA_ARGS+=("$1")
            shift
            ;;
    esac
done

# =============================================================================
# MAIN
# =============================================================================

main() {
    log_step "Building Docker image: $FULL_IMAGE"
    init_common

    # Validate requirements
    require_buildx

    # Check if Dockerfile exists
    if [[ ! -f "$DOCKERFILE" ]]; then
        log_warn "Dockerfile not found at $DOCKERFILE, checking for alternatives..."
        if [[ -f "docker/Dockerfile" ]]; then
            DOCKERFILE="docker/Dockerfile"
            log_info "Using: $DOCKERFILE"
        else
            log_error "No Dockerfile found"
            exit 1
        fi
    fi

    # Ensure buildx builder exists
    ensure_buildx_builder "superset-builder"

    # Build labels
    local build_date
    build_date="$(timestamp)"
    local vcs_ref
    vcs_ref="$(git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"

    # Build command
    local build_cmd=(
        docker buildx build
        --platform "$PLATFORMS"
        --tag "$FULL_IMAGE"
        --label "org.opencontainers.image.created=$build_date"
        --label "org.opencontainers.image.revision=$vcs_ref"
        --label "org.opencontainers.image.source=https://github.com/jgtolentino/superset"
        --label "org.opencontainers.image.title=ipai-superset"
        --label "org.opencontainers.image.vendor=InsightPulse AI"
        --file "$DOCKERFILE"
        --progress plain
    )

    # Add push/load flags
    if [[ -n "$PUSH_FLAG" ]]; then
        build_cmd+=("$PUSH_FLAG")
    fi
    if [[ -n "$LOAD_FLAG" ]]; then
        build_cmd+=("$LOAD_FLAG")
    fi

    # Add any extra args
    build_cmd+=("${EXTRA_ARGS[@]}")

    # Add build context
    build_cmd+=("$BUILD_CONTEXT")

    log_info "Build command:"
    echo "  ${build_cmd[*]}"
    echo ""

    # Execute build
    if "${build_cmd[@]}"; then
        log_success "Build completed successfully"

        # Show image info if loaded
        if [[ -n "$LOAD_FLAG" ]] && image_exists_locally "$FULL_IMAGE"; then
            echo ""
            log_info "Image details:"
            docker images "$IMAGE_REPO" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
        fi
    else
        log_error "Build failed"
        exit 1
    fi
}

main "$@"
