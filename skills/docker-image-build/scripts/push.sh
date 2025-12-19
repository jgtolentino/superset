#!/usr/bin/env bash
# Push Docker image to registry
#
# Usage:
#   ./push.sh [--dry-run]
#
# Environment variables:
#   IMAGE_REPO   - Image repository (must include registry prefix)
#   IMAGE_TAG    - Image tag
#   GITHUB_TOKEN - Token for GHCR authentication (optional if already logged in)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# =============================================================================
# DEFAULTS
# =============================================================================

DRY_RUN=false

# =============================================================================
# PARSE ARGUMENTS
# =============================================================================

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        *)
            log_error "Unknown argument: $1"
            exit 1
            ;;
    esac
done

# =============================================================================
# REGISTRY LOGIN
# =============================================================================

login_ghcr() {
    local token="${GITHUB_TOKEN:-}"

    if [[ -z "$token" ]]; then
        log_warn "GITHUB_TOKEN not set, assuming already authenticated"
        return 0
    fi

    log_info "Logging into ghcr.io..."
    echo "$token" | docker login ghcr.io -u "$(echo "$IMAGE_REPO" | cut -d'/' -f2)" --password-stdin
    log_success "Logged into ghcr.io"
}

# =============================================================================
# PUSH
# =============================================================================

push_image() {
    local image="$1"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_warn "[DRY-RUN] Would push: $image"
        return 0
    fi

    log_step "Pushing: $image"

    if docker push "$image"; then
        log_success "Pushed: $image"

        # Show digest
        local digest
        digest="$(get_image_digest "$image")"
        if [[ -n "$digest" ]]; then
            log_info "Digest: $digest"
        fi
    else
        log_error "Failed to push: $image"
        return 1
    fi
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    log_step "Push Docker image: $FULL_IMAGE"
    init_common

    require_docker

    # Verify image exists locally
    if ! image_exists_locally "$FULL_IMAGE"; then
        log_error "Image not found locally: $FULL_IMAGE"
        log_info "Run 'make image-build --load' first"
        exit 1
    fi

    # Login to registry if GHCR
    if [[ "$IMAGE_REPO" == ghcr.io/* ]]; then
        login_ghcr
    fi

    # Push image
    push_image "$FULL_IMAGE"

    # Also push as latest if this is a versioned tag
    if [[ "$IMAGE_TAG" != "latest" && "$IMAGE_TAG" =~ ^v?[0-9] ]]; then
        local latest_image="${IMAGE_REPO}:latest"
        log_info "Also tagging as latest..."
        docker tag "$FULL_IMAGE" "$latest_image"
        push_image "$latest_image"
    fi

    echo ""
    log_success "Push complete!"
}

main "$@"
