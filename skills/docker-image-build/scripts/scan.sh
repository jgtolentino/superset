#!/usr/bin/env bash
# Scan Docker image for vulnerabilities
# Uses Docker Scout if available, falls back to Trivy
#
# Usage:
#   ./scan.sh [--format json|sarif|table] [--severity critical,high]
#
# Environment variables:
#   IMAGE_REPO   - Image repository
#   IMAGE_TAG    - Image tag
#   SECURITY_OUTPUT_DIR - Output directory for scan results

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# =============================================================================
# DEFAULTS
# =============================================================================

OUTPUT_FORMAT="table"
SEVERITY_FILTER="critical,high,medium"
SCANNER=""

# =============================================================================
# PARSE ARGUMENTS
# =============================================================================

while [[ $# -gt 0 ]]; do
    case "$1" in
        --format)
            OUTPUT_FORMAT="$2"
            shift 2
            ;;
        --severity)
            SEVERITY_FILTER="$2"
            shift 2
            ;;
        --scanner)
            SCANNER="$2"
            shift 2
            ;;
        *)
            log_error "Unknown argument: $1"
            exit 1
            ;;
    esac
done

# =============================================================================
# SCANNER DETECTION
# =============================================================================

detect_scanner() {
    if [[ -n "$SCANNER" ]]; then
        echo "$SCANNER"
        return
    fi

    # Prefer Docker Scout if available
    if docker scout version &>/dev/null 2>&1; then
        echo "scout"
        return
    fi

    # Fall back to Trivy
    if command -v trivy &>/dev/null; then
        echo "trivy"
        return
    fi

    # No scanner available
    echo "none"
}

# =============================================================================
# DOCKER SCOUT SCAN
# =============================================================================

scan_with_scout() {
    local image="$1"
    local output_json="$SECURITY_OUTPUT_DIR/scout-results.json"
    local output_sarif="$SECURITY_OUTPUT_DIR/scout-results.sarif"

    log_step "Scanning with Docker Scout: $image"

    # Run Scout CVE scan
    case "$OUTPUT_FORMAT" in
        json)
            docker scout cves "$image" --format json --output "$output_json" 2>/dev/null || {
                # Fallback: capture stdout if --output not supported
                docker scout cves "$image" --format json > "$output_json" 2>/dev/null
            }
            log_success "JSON output: $output_json"
            ;;
        sarif)
            docker scout cves "$image" --format sarif --output "$output_sarif" 2>/dev/null || {
                docker scout cves "$image" --format sarif > "$output_sarif" 2>/dev/null
            }
            log_success "SARIF output: $output_sarif"
            ;;
        table|*)
            docker scout cves "$image" --format packages
            # Also generate JSON for artifacts
            docker scout cves "$image" --format json > "$output_json" 2>/dev/null || true
            ;;
    esac

    # Generate quickview
    echo ""
    log_info "Quick overview:"
    docker scout quickview "$image" 2>/dev/null || true

    return 0
}

# =============================================================================
# TRIVY SCAN
# =============================================================================

scan_with_trivy() {
    local image="$1"
    local output_json="$SECURITY_OUTPUT_DIR/trivy-results.json"
    local output_sarif="$SECURITY_OUTPUT_DIR/trivy-results.sarif"
    local severity_upper
    severity_upper="$(echo "$SEVERITY_FILTER" | tr '[:lower:]' '[:upper:]')"

    log_step "Scanning with Trivy: $image"

    case "$OUTPUT_FORMAT" in
        json)
            trivy image --format json --output "$output_json" \
                --severity "$severity_upper" \
                "$image"
            log_success "JSON output: $output_json"
            ;;
        sarif)
            trivy image --format sarif --output "$output_sarif" \
                --severity "$severity_upper" \
                "$image"
            log_success "SARIF output: $output_sarif"
            ;;
        table|*)
            trivy image --format table \
                --severity "$severity_upper" \
                "$image"
            # Also generate JSON and SARIF for artifacts
            trivy image --format json --output "$output_json" \
                --severity "$severity_upper" \
                "$image" 2>/dev/null || true
            trivy image --format sarif --output "$output_sarif" \
                --severity "$severity_upper" \
                "$image" 2>/dev/null || true
            ;;
    esac

    return 0
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    log_step "Security scan: $FULL_IMAGE"
    init_common

    require_docker

    # Detect available scanner
    local scanner
    scanner="$(detect_scanner)"

    case "$scanner" in
        scout)
            log_info "Using Docker Scout"
            scan_with_scout "$FULL_IMAGE"
            ;;
        trivy)
            log_info "Using Trivy (Docker Scout not available)"
            scan_with_trivy "$FULL_IMAGE"
            ;;
        none)
            log_warn "No vulnerability scanner available"
            log_info "Install Docker Scout: docker scout --help"
            log_info "Install Trivy: https://aquasecurity.github.io/trivy/"
            echo ""
            log_info "Skipping vulnerability scan"

            # Create placeholder output
            cat > "$SECURITY_OUTPUT_DIR/scan-skipped.json" <<EOF
{
  "status": "skipped",
  "reason": "No scanner available (Docker Scout or Trivy)",
  "image": "$FULL_IMAGE",
  "timestamp": "$(timestamp)"
}
EOF
            return 0
            ;;
    esac

    echo ""
    log_success "Scan complete. Results in: $SECURITY_OUTPUT_DIR/"
    ls -la "$SECURITY_OUTPUT_DIR/" 2>/dev/null || true
}

main "$@"
