#!/usr/bin/env bash
# =============================================================================
# Codex Cloud Environment Setup Script
# Repository: jgtolentino/superset
# Purpose: Configure Codex cloud environment for Superset infra/config repo
# =============================================================================
#
# IMPORTANT: This repo is INFRASTRUCTURE/CONFIG for Superset, NOT the Superset
# Python package itself. We install Superset from PyPI, not from this repo.
#
# =============================================================================
set -euo pipefail

echo "=== Codex Setup: jgtolentino/superset ==="

# Navigate to workspace
cd /workspace/superset 2>/dev/null || cd "$(dirname "$0")/.." || {
    echo "ERROR: Cannot find workspace directory"
    exit 1
}

REPO_ROOT="$(pwd)"
echo "Working directory: $REPO_ROOT"

# -----------------------------------------------------------------------------
# 1. Python Virtual Environment
# -----------------------------------------------------------------------------
echo ""
echo "=== Step 1: Setting up Python environment ==="

python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip wheel setuptools --quiet

# -----------------------------------------------------------------------------
# 2. Install Superset from PyPI (NOT this repo)
# -----------------------------------------------------------------------------
echo ""
echo "=== Step 2: Installing Apache Superset from PyPI ==="

# This repo is infra/config - Superset itself comes from PyPI
# Pin to a specific version for reproducibility (update as needed)
SUPERSET_VERSION="${SUPERSET_VERSION:-4.0.1}"
echo "Installing apache-superset==$SUPERSET_VERSION"

pip install "apache-superset==$SUPERSET_VERSION" --quiet

# -----------------------------------------------------------------------------
# 3. Install repo-specific dependencies
# -----------------------------------------------------------------------------
echo ""
echo "=== Step 3: Installing repo dependencies ==="

if [ -f "$REPO_ROOT/requirements.txt" ]; then
    echo "Found requirements.txt, installing..."
    pip install -r "$REPO_ROOT/requirements.txt" --quiet
else
    echo "No requirements.txt found, skipping."
fi

# Install dev/test dependencies if they exist
if [ -f "$REPO_ROOT/requirements-dev.txt" ]; then
    echo "Found requirements-dev.txt, installing..."
    pip install -r "$REPO_ROOT/requirements-dev.txt" --quiet
fi

# -----------------------------------------------------------------------------
# 4. Node.js / Frontend (if superset-frontend exists in repo)
# -----------------------------------------------------------------------------
echo ""
echo "=== Step 4: Checking for frontend dependencies ==="

if [ -d "$REPO_ROOT/superset-frontend" ]; then
    echo "Found superset-frontend/, installing npm dependencies..."
    cd "$REPO_ROOT/superset-frontend"
    if command -v npm >/dev/null 2>&1; then
        npm ci 2>/dev/null || npm install --quiet
    else
        echo "WARNING: npm not found, skipping frontend setup"
    fi
    cd "$REPO_ROOT"
else
    echo "No superset-frontend/ directory found, skipping."
fi

# -----------------------------------------------------------------------------
# 5. Playwright for E2E testing (if configured)
# -----------------------------------------------------------------------------
echo ""
echo "=== Step 5: Setting up Playwright (if applicable) ==="

if [ -f "$REPO_ROOT/playwright.config.ts" ] || [ -f "$REPO_ROOT/playwright.config.js" ]; then
    echo "Found Playwright config, installing..."
    if command -v npm >/dev/null 2>&1; then
        npm install --quiet 2>/dev/null || true
        npx playwright install chromium --quiet 2>/dev/null || true
    fi
else
    echo "No Playwright config found, skipping."
fi

# -----------------------------------------------------------------------------
# 6. Superset Database Bootstrap (SQLite for Codex container)
# -----------------------------------------------------------------------------
echo ""
echo "=== Step 6: Bootstrap Superset DB (optional) ==="

# Set minimal environment for Superset CLI
export SUPERSET_ENV="${SUPERSET_ENV:-development}"
export FLASK_APP="${FLASK_APP:-superset}"

# Only bootstrap if explicitly requested (to avoid long setup times)
if [ "${SUPERSET_BOOTSTRAP_DB:-false}" = "true" ]; then
    echo "SUPERSET_BOOTSTRAP_DB=true, initializing database..."
    superset db upgrade || echo "WARNING: superset db upgrade failed (may be expected in some environments)"
    superset init || echo "WARNING: superset init failed (may be expected in some environments)"
else
    echo "Skipping DB bootstrap (set SUPERSET_BOOTSTRAP_DB=true to enable)"
fi

# -----------------------------------------------------------------------------
# 7. Validate environment
# -----------------------------------------------------------------------------
echo ""
echo "=== Step 7: Validating setup ==="

# Check if key tools are available
echo -n "Python: "; python3 --version
echo -n "Pip: "; pip --version | head -c 50; echo "..."
echo -n "Superset: "; superset --version 2>/dev/null || echo "not in PATH (may need activation)"

# Run repo validation script if it exists
if [ -x "$REPO_ROOT/scripts/validate.sh" ]; then
    echo ""
    echo "Running repo validation..."
    "$REPO_ROOT/scripts/validate.sh" || echo "WARNING: Validation script reported issues"
fi

# -----------------------------------------------------------------------------
# Done
# -----------------------------------------------------------------------------
echo ""
echo "=== Codex Setup Complete ==="
echo ""
echo "Environment ready. Key paths:"
echo "  Repo root:    $REPO_ROOT"
echo "  Python venv:  $REPO_ROOT/.venv"
echo "  Activate:     source $REPO_ROOT/.venv/bin/activate"
echo ""
echo "This repo contains Superset INFRASTRUCTURE (not the app code):"
echo "  - infra/do/       DigitalOcean deployment specs"
echo "  - infra/superset/ Superset config & Dockerfile"
echo "  - scripts/        Automation & utility scripts"
echo "  - examples/       Dashboard & dataset examples"
echo ""
