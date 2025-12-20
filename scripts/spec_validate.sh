#!/usr/bin/env bash
# Spec Kit Validator
# Validates that all spec kits have required files and content quality
#
# Usage: ./scripts/spec_validate.sh [--strict]
#   --strict: Fail on warnings (missing optional files)

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $*"; }
log_ok() { echo -e "${GREEN}[OK]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }

STRICT="${1:-}"
fail=0
warn=0

# Check spec/ directory exists
if [ ! -d "spec" ]; then
    log_error "Missing spec/ directory"
    exit 1
fi

# Find all spec bundles (directories containing constitution.md)
bundles=$(find spec -mindepth 2 -maxdepth 2 -type f -name constitution.md -print 2>/dev/null | wc -l | tr -d ' ')

if [ "$bundles" -lt 1 ]; then
    log_error "No spec kit bundles found. Expected spec/<slug>/constitution.md"
    exit 1
fi

log_info "Found $bundles spec kit bundle(s)"
echo ""

# Required files for each spec kit
REQUIRED_FILES=("constitution.md" "prd.md" "plan.md" "tasks.md")

# Minimum non-empty, non-heading lines per file
MIN_CONTENT_LINES=10

# Placeholder patterns to reject
# Match standalone TODO/TBD markers that indicate unfinished work, not references in documentation
# Examples that SHOULD match:
#   - "TODO: fix this"
#   - "# TODO"
#   - "TBD - needs work"
#   - "PLACEHOLDER"
# Examples that should NOT match:
#   - "Flag placeholders (TODO/TBD/LOREM)"
#   - "description: TODO/TBD blocked"
#   - "No Placeholders in Specs"
# We match: start of line (optional whitespace/comment) + keyword + colon/dash/whitespace
PLACEHOLDER_PATTERN='^[[:space:]]*(#[[:space:]]*)?(TODO|TBD)[[:space:]]*[:\-]|^[[:space:]]*PLACEHOLDER[[:space:]]*$|FILL[[:space:]]+ME[[:space:]]+IN|LOREM[[:space:]]+IPSUM'

# Validate each spec bundle
while IFS= read -r cfile; do
    slug_dir="$(dirname "$cfile")"
    slug_name="$(basename "$slug_dir")"

    log_info "Validating: $slug_name"

    for f in "${REQUIRED_FILES[@]}"; do
        path="$slug_dir/$f"

        # Check file exists
        if [ ! -f "$path" ]; then
            log_error "Missing required file: $path"
            fail=1
            continue
        fi

        # Check non-trivial content (excluding empty lines and headings)
        non_empty=$(grep -Ev '^\s*$' "$path" | grep -Ev '^#+[[:space:]]' | wc -l | tr -d ' ')
        if [ "$non_empty" -lt "$MIN_CONTENT_LINES" ]; then
            log_error "$path: Too small ($non_empty lines, need $MIN_CONTENT_LINES+)"
            fail=1
        fi

        # Check for placeholder text
        if grep -Eqi "$PLACEHOLDER_PATTERN" "$path"; then
            log_error "$path: Contains placeholders (TODO/TBD/etc)"
            fail=1
        fi

        # All checks passed for this file
        if [ "$fail" -eq 0 ] || ! grep -q "$path" <<< "$fail"; then
            log_ok "$f"
        fi
    done

    echo ""
done < <(find spec -mindepth 2 -maxdepth 2 -type f -name constitution.md -print)

# Check CLAUDE.md exists
if [ ! -f "CLAUDE.md" ]; then
    log_warn "Missing CLAUDE.md at repo root"
    warn=1
else
    log_ok "CLAUDE.md exists"
fi

# Check agent configuration
if [ ! -f ".claude/settings.json" ]; then
    log_warn "Missing .claude/settings.json (agent allowlist)"
    warn=1
else
    log_ok ".claude/settings.json exists"
fi

if [ ! -d ".claude/commands" ]; then
    log_warn "Missing .claude/commands/ (agent commands)"
    warn=1
else
    cmd_count=$(find .claude/commands -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
    log_ok ".claude/commands/ exists ($cmd_count commands)"
fi

echo ""

# Final status
if [ "$fail" -ne 0 ]; then
    log_error "Spec Kit validation FAILED"
    exit 1
fi

if [ "$warn" -ne 0 ] && [ "$STRICT" = "--strict" ]; then
    log_error "Spec Kit validation FAILED (strict mode)"
    exit 1
fi

if [ "$warn" -ne 0 ]; then
    log_warn "Spec Kit validation passed with warnings"
    exit 0
fi

log_ok "Spec Kit validation PASSED"
exit 0
