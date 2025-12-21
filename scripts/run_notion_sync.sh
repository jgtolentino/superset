#!/bin/bash
# run_notion_sync.sh - Run Notion sync to Databricks
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Source environment validation
source "$SCRIPT_DIR/require_env.sh" 2>/dev/null || {
    echo "Warning: require_env.sh not found, skipping validation"
}

echo "==================================="
echo " Notion Sync Service"
echo "==================================="

# Navigate to service directory
cd "$ROOT_DIR/services/notion-sync"

# Check for virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install/update dependencies
pip install -e . -q

# Check for .env file
if [ ! -f ".env" ]; then
    echo "Error: .env file not found"
    echo "Copy .env.example to .env and fill in your credentials"
    exit 1
fi

# Load environment variables
set -a
source .env
set +a

# Validate required environment variables
REQUIRED_VARS=(
    "NOTION_API_KEY"
    "DATABRICKS_HOST"
    "DATABRICKS_TOKEN"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: Missing required environment variable: $var"
        exit 1
    fi
done

# Check for suspicious placeholder values
for var in "${REQUIRED_VARS[@]}"; do
    value="${!var}"
    if [[ "$value" == "changeme" ]] || \
       [[ "$value" == "your-"* ]] || \
       [[ "$value" == *"xxx"* ]]; then
        echo "Error: Suspicious placeholder value in $var"
        exit 1
    fi
done

echo "Environment validated successfully"
echo ""

# Parse arguments
FULL_REFRESH=""
DATABASE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --full-refresh)
            FULL_REFRESH="--full-refresh"
            shift
            ;;
        -d|--database)
            DATABASE="-d $2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --full-refresh    Ignore watermarks and sync all data"
            echo "  -d, --database    Sync specific database only"
            echo "  --help            Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Run sync
echo "Starting Notion sync..."
echo ""

notion-sync sync $FULL_REFRESH $DATABASE

echo ""
echo "Sync complete!"
