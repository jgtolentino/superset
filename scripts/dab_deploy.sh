#!/bin/bash
# dab_deploy.sh - Deploy Databricks Asset Bundle
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "==================================="
echo " Databricks Bundle Deployment"
echo "==================================="

# Default target
TARGET="${1:-dev}"

# Validate target
case $TARGET in
    dev|staging|prod)
        echo "Target: $TARGET"
        ;;
    *)
        echo "Invalid target: $TARGET"
        echo "Usage: $0 [dev|staging|prod]"
        exit 1
        ;;
esac

# Check Databricks CLI
if ! command -v databricks &> /dev/null; then
    echo "Error: Databricks CLI not installed"
    echo "Install with: curl -fsSL https://raw.githubusercontent.com/databricks/setup-cli/main/install.sh | sh"
    exit 1
fi

# Check credentials
if [ -z "$DATABRICKS_HOST" ] || [ -z "$DATABRICKS_TOKEN" ]; then
    echo "Error: DATABRICKS_HOST and DATABRICKS_TOKEN must be set"
    echo ""
    echo "Set via environment variables:"
    echo "  export DATABRICKS_HOST=https://your-workspace.azuredatabricks.net"
    echo "  export DATABRICKS_TOKEN=your-token"
    exit 1
fi

# Navigate to bundle directory
cd "$ROOT_DIR/infra/databricks"

echo ""
echo "Validating bundle..."
databricks bundle validate -t "$TARGET"

echo ""
echo "Deploying bundle..."
databricks bundle deploy -t "$TARGET"

echo ""
echo "Listing deployed jobs..."
databricks bundle run -t "$TARGET" --list

echo ""
echo "==================================="
echo " Deployment Complete"
echo "==================================="
echo ""
echo "To run a specific job:"
echo "  databricks bundle run -t $TARGET [job_name]"
echo ""
echo "Example:"
echo "  databricks bundle run -t $TARGET notion_sync_bronze"
