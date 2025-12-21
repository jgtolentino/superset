#!/bin/bash
# dev_up.sh - Start local development environment for Control Room
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo "==================================="
echo " PPM Control Room - Local Dev Setup"
echo "==================================="

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
check_prereqs() {
    echo -e "\n${YELLOW}Checking prerequisites...${NC}"

    if ! command -v node &> /dev/null; then
        echo -e "${RED}Node.js is not installed. Please install Node.js 18+${NC}"
        exit 1
    fi

    NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 18 ]; then
        echo -e "${RED}Node.js version must be 18+. Current: $(node -v)${NC}"
        exit 1
    fi
    echo -e "  ${GREEN}Node.js: $(node -v)${NC}"

    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Python 3 is not installed.${NC}"
        exit 1
    fi
    echo -e "  ${GREEN}Python: $(python3 --version)${NC}"

    echo -e "  ${GREEN}All prerequisites met${NC}"
}

# Setup Control Room
setup_control_room() {
    echo -e "\n${YELLOW}Setting up Control Room...${NC}"

    cd "$ROOT_DIR/apps/control-room"

    if [ ! -f ".env.local" ]; then
        echo "Creating .env.local from template..."
        if [ -f ".env.example" ]; then
            cp .env.example .env.local
            echo "MOCK_DATA=true" >> .env.local
        else
            cat > .env.local << EOF
# Local development environment
MOCK_DATA=true
DATABRICKS_HOST=
DATABRICKS_TOKEN=
DATABRICKS_HTTP_PATH=
DATABRICKS_CATALOG=main
NOTION_API_KEY=
NOTION_ACTIONS_DB_ID=
EOF
        fi
        echo -e "  ${GREEN}Created .env.local${NC}"
    else
        echo -e "  ${GREEN}.env.local already exists${NC}"
    fi

    # Install dependencies
    echo "Installing npm dependencies..."
    npm install

    echo -e "  ${GREEN}Control Room setup complete${NC}"
}

# Setup Notion Sync
setup_notion_sync() {
    echo -e "\n${YELLOW}Setting up Notion Sync service...${NC}"

    cd "$ROOT_DIR/services/notion-sync"

    if [ ! -f ".env" ]; then
        echo "Creating .env from template..."
        if [ -f ".env.example" ]; then
            cp .env.example .env
        fi
        echo -e "  ${YELLOW}Created .env - please fill in your credentials${NC}"
    else
        echo -e "  ${GREEN}.env already exists${NC}"
    fi

    # Create virtual environment
    if [ ! -d ".venv" ]; then
        echo "Creating Python virtual environment..."
        python3 -m venv .venv
    fi

    # Install dependencies
    echo "Installing Python dependencies..."
    source .venv/bin/activate
    pip install -e ".[dev]" -q
    deactivate

    echo -e "  ${GREEN}Notion Sync setup complete${NC}"
}

# Start services
start_services() {
    echo -e "\n${YELLOW}Starting services...${NC}"

    # Start Control Room in background
    cd "$ROOT_DIR/apps/control-room"
    echo "Starting Control Room on http://localhost:3000..."
    npm run dev &
    CONTROL_ROOM_PID=$!

    echo -e "\n${GREEN}==================================="
    echo "Services started!"
    echo "==================================="
    echo ""
    echo "Control Room: http://localhost:3000"
    echo ""
    echo "Press Ctrl+C to stop all services"
    echo -e "===================================${NC}"

    # Wait for interrupt
    trap "kill $CONTROL_ROOM_PID 2>/dev/null; exit 0" SIGINT SIGTERM
    wait $CONTROL_ROOM_PID
}

# Main
main() {
    check_prereqs
    setup_control_room
    setup_notion_sync

    echo -e "\n${GREEN}Development environment ready!${NC}"
    echo ""
    echo "To start the Control Room UI:"
    echo "  cd apps/control-room && npm run dev"
    echo ""
    echo "To run the Notion sync service:"
    echo "  cd services/notion-sync"
    echo "  source .venv/bin/activate"
    echo "  notion-sync sync"
    echo ""

    # Ask to start services
    read -p "Start Control Room now? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        start_services
    fi
}

main "$@"
