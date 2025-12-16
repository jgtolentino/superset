#!/usr/bin/env bash
set -euo pipefail

# Preflight Environment Variable Check
# Validates all required credentials are set before script execution
# Returns exit code 2 if missing vars, exit code 3 if suspicious defaults

REQ=(
  BASE_URL
  SUPERSET_ADMIN_USER
  SUPERSET_ADMIN_PASS
  EXAMPLES_DB_URI
)

# Check for missing/empty required vars
for v in "${REQ[@]}"; do
  if [[ -z "${!v:-}" ]]; then
    echo "❌ BLOCKED: missing env var $v" >&2
    echo "" >&2
    echo "Required environment variables:" >&2
    echo "  - BASE_URL" >&2
    echo "  - SUPERSET_ADMIN_USER" >&2
    echo "  - SUPERSET_ADMIN_PASS" >&2
    echo "  - EXAMPLES_DB_URI" >&2
    echo "" >&2
    echo "Set these in ~/.zshrc or export before running script" >&2
    exit 2
  fi
done

# Prevent obvious placeholder values in passwords
# Note: Only blocks generic/documentation placeholders, not actual production values
SUSPICIOUS_PASSWORDS=(
  "password"
  "changeme"
  "your_admin_password"
  "your_password"
  "example"
  "test"
  "INSERT_PASSWORD_HERE"
  "CHANGE_ME"
)

# Only check password for obvious placeholders
val="${SUPERSET_ADMIN_PASS}"
for sus in "${SUSPICIOUS_PASSWORDS[@]}"; do
  if [[ "${val,,}" == "${sus,,}" ]]; then  # Case-insensitive comparison
    echo "❌ BLOCKED: obvious placeholder in SUPERSET_ADMIN_PASS: '$val'" >&2
    echo "" >&2
    echo "This is a documentation placeholder, not a real credential." >&2
    echo "Set actual production credentials in ~/.zshrc" >&2
    exit 3
  fi
done

# All checks passed
echo "✅ env=OK (all required credentials validated)"
