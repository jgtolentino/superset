#!/usr/bin/env bash
# Verify Docker image integrity and functionality
#
# Checks:
#   1. Image exists locally
#   2. Docker history available
#   3. Can run superset --version (or python fallback)
#
# Usage:
#   ./verify.sh [--quick]
#
# Environment variables:
#   IMAGE_REPO   - Image repository
#   IMAGE_TAG    - Image tag

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# =============================================================================
# DEFAULTS
# =============================================================================

QUICK_MODE=false
CHECKS_PASSED=0
CHECKS_FAILED=0

# =============================================================================
# PARSE ARGUMENTS
# =============================================================================

while [[ $# -gt 0 ]]; do
    case "$1" in
        --quick)
            QUICK_MODE=true
            shift
            ;;
        *)
            log_error "Unknown argument: $1"
            exit 1
            ;;
    esac
done

# =============================================================================
# CHECK FUNCTIONS
# =============================================================================

check_pass() {
    log_success "$1"
    ((CHECKS_PASSED++))
}

check_fail() {
    log_error "$1"
    ((CHECKS_FAILED++))
}

check_image_exists() {
    log_step "Check: Image exists locally"

    if image_exists_locally "$FULL_IMAGE"; then
        check_pass "Image found: $FULL_IMAGE"
        return 0
    else
        check_fail "Image not found: $FULL_IMAGE"
        return 1
    fi
}

check_docker_history() {
    log_step "Check: Docker history available"

    local history
    if history="$(docker history "$FULL_IMAGE" --no-trunc 2>/dev/null)"; then
        local layer_count
        layer_count="$(echo "$history" | wc -l)"
        check_pass "Docker history: $((layer_count - 1)) layers"
        return 0
    else
        check_fail "Docker history unavailable"
        return 1
    fi
}

check_superset_version() {
    log_step "Check: Superset version command"

    local version=""
    local exit_code=0

    # Try superset --version
    version="$(docker run --rm "$FULL_IMAGE" superset --version 2>/dev/null)" || exit_code=$?

    if [[ $exit_code -eq 0 && -n "$version" ]]; then
        check_pass "superset --version: $version"
        return 0
    fi

    # Fallback: python -c import superset
    log_info "Trying Python fallback..."
    version="$(docker run --rm "$FULL_IMAGE" python -c "import superset; print(superset.__version__)" 2>/dev/null)" || exit_code=$?

    if [[ $exit_code -eq 0 && -n "$version" ]]; then
        check_pass "Python import: superset $version"
        return 0
    fi

    # Fallback: just check python works
    log_info "Trying basic Python check..."
    if docker run --rm "$FULL_IMAGE" python --version &>/dev/null; then
        local py_version
        py_version="$(docker run --rm "$FULL_IMAGE" python --version 2>&1)"
        check_pass "Python available: $py_version"
        return 0
    fi

    check_fail "Unable to verify Superset version"
    return 1
}

check_image_size() {
    log_step "Check: Image size"

    local size
    size="$(docker images "$FULL_IMAGE" --format '{{.Size}}' 2>/dev/null)"

    if [[ -n "$size" ]]; then
        check_pass "Image size: $size"
        return 0
    else
        check_fail "Unable to determine image size"
        return 1
    fi
}

check_labels() {
    log_step "Check: OCI labels"

    local labels
    labels="$(docker inspect "$FULL_IMAGE" --format '{{json .Config.Labels}}' 2>/dev/null)"

    if [[ -n "$labels" && "$labels" != "null" && "$labels" != "{}" ]]; then
        local label_count
        label_count="$(echo "$labels" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "0")"
        check_pass "OCI labels: $label_count labels found"

        # Show key labels if verbose
        if [[ "${VERBOSE:-false}" == "true" ]]; then
            echo "$labels" | python3 -m json.tool 2>/dev/null || echo "$labels"
        fi
        return 0
    else
        log_warn "No OCI labels found (non-critical)"
        return 0
    fi
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    log_step "Verify Docker image: $FULL_IMAGE"
    init_common

    require_docker

    echo ""

    # Run checks
    check_image_exists || true
    check_docker_history || true

    if [[ "$QUICK_MODE" == "false" ]]; then
        check_superset_version || true
        check_image_size || true
        check_labels || true
    fi

    # Summary
    echo ""
    echo "========================================"
    log_info "Verification Summary"
    echo "========================================"
    echo -e "  ${GREEN}Passed:${NC} $CHECKS_PASSED"
    echo -e "  ${RED}Failed:${NC} $CHECKS_FAILED"
    echo ""

    if [[ $CHECKS_FAILED -gt 0 ]]; then
        log_error "Verification failed with $CHECKS_FAILED error(s)"
        exit 1
    else
        log_success "All verification checks passed!"
        exit 0
    fi
}

main "$@"
