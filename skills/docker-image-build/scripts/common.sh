#!/usr/bin/env bash
# Common utilities for Docker image build skill
# Source this file in other scripts: source "$(dirname "$0")/common.sh"

set -euo pipefail

# =============================================================================
# ENVIRONMENT DEFAULTS
# =============================================================================

export IMAGE_REPO="${IMAGE_REPO:-ghcr.io/jgtolentino/ipai-superset}"
export IMAGE_TAG="${IMAGE_TAG:-latest}"
export PLATFORMS="${PLATFORMS:-linux/amd64,linux/arm64}"
export DOCKERFILE="${DOCKERFILE:-Dockerfile}"
export BUILD_CONTEXT="${BUILD_CONTEXT:-.}"

# Derived
export FULL_IMAGE="${IMAGE_REPO}:${IMAGE_TAG}"

# Output directories
export SECURITY_OUTPUT_DIR="${SECURITY_OUTPUT_DIR:-tools/security/output}"

# =============================================================================
# COLORS
# =============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# =============================================================================
# LOGGING
# =============================================================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $*"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

log_step() {
    echo -e "${CYAN}==>${NC} $*"
}

# =============================================================================
# VALIDATION
# =============================================================================

require_command() {
    local cmd="$1"
    if ! command -v "$cmd" &>/dev/null; then
        log_error "Required command not found: $cmd"
        return 1
    fi
}

require_docker() {
    require_command docker
    if ! docker info &>/dev/null; then
        log_error "Docker daemon is not running"
        return 1
    fi
}

require_buildx() {
    require_docker
    if ! docker buildx version &>/dev/null; then
        log_error "Docker buildx is not available"
        return 1
    fi
}

require_env() {
    local var_name="$1"
    if [[ -z "${!var_name:-}" ]]; then
        log_error "Required environment variable not set: $var_name"
        return 1
    fi
}

# =============================================================================
# BUILDX HELPERS
# =============================================================================

ensure_buildx_builder() {
    local builder_name="${1:-multiarch-builder}"

    if ! docker buildx inspect "$builder_name" &>/dev/null; then
        log_info "Creating buildx builder: $builder_name"
        docker buildx create --name "$builder_name" --driver docker-container --bootstrap
    fi

    docker buildx use "$builder_name"
    log_success "Using buildx builder: $builder_name"
}

# =============================================================================
# IMAGE HELPERS
# =============================================================================

image_exists_locally() {
    local image="$1"
    docker image inspect "$image" &>/dev/null
}

image_exists_remote() {
    local image="$1"
    docker manifest inspect "$image" &>/dev/null 2>&1
}

get_image_digest() {
    local image="$1"
    docker inspect --format='{{index .RepoDigests 0}}' "$image" 2>/dev/null || echo ""
}

get_image_id() {
    local image="$1"
    docker inspect --format='{{.Id}}' "$image" 2>/dev/null || echo ""
}

# =============================================================================
# OUTPUT HELPERS
# =============================================================================

ensure_output_dir() {
    mkdir -p "$SECURITY_OUTPUT_DIR"
}

timestamp() {
    date -u +"%Y-%m-%dT%H:%M:%SZ"
}

# =============================================================================
# CLEANUP
# =============================================================================

cleanup_dangling_images() {
    log_info "Cleaning up dangling images..."
    docker image prune -f &>/dev/null || true
}

# =============================================================================
# INITIALIZATION
# =============================================================================

init_common() {
    log_info "Image: $FULL_IMAGE"
    log_info "Platforms: $PLATFORMS"
    ensure_output_dir
}
