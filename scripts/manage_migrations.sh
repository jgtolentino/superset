#!/usr/bin/env bash
set -euo pipefail

# Database Migration Management Script
# Creates, applies, and manages database migrations using Flask-Migrate

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# ============================================================================
# USAGE
# ============================================================================

usage() {
    cat << EOF
Database Migration Management

Usage: $0 <command> [options]

Commands:
    init            Initialize migrations directory (first time only)
    create <name>   Create a new migration with given name
    upgrade         Apply all pending migrations
    downgrade       Rollback last migration
    current         Show current migration version
    history         Show migration history
    status          Show migration status

Environment Variables (required):
    SUPERSET__SQLALCHEMY_DATABASE_URI  or  SQLALCHEMY_DATABASE_URI

Examples:
    $0 init
    $0 create "add user table"
    $0 upgrade
    $0 current
    $0 history

EOF
    exit 1
}

# ============================================================================
# ENVIRONMENT CHECK
# ============================================================================

check_database_uri() {
    if [[ -z "${SUPERSET__SQLALCHEMY_DATABASE_URI:-}" ]] && [[ -z "${SQLALCHEMY_DATABASE_URI:-}" ]]; then
        echo "❌ BLOCKED: missing database URI environment variable" >&2
        echo "" >&2
        echo "Set one of:" >&2
        echo "  - SUPERSET__SQLALCHEMY_DATABASE_URI (preferred)" >&2
        echo "  - SQLALCHEMY_DATABASE_URI (fallback)" >&2
        echo "" >&2
        exit 2
    fi
    
    DB_URI="${SUPERSET__SQLALCHEMY_DATABASE_URI:-${SQLALCHEMY_DATABASE_URI}}"
    
    # Verify it's PostgreSQL (not SQLite)
    if [[ "$DB_URI" == sqlite* ]]; then
        echo "❌ ERROR: SQLite not supported for migrations" >&2
        echo "   Use PostgreSQL for metadata database" >&2
        exit 1
    fi
    
    echo "✅ Database URI configured (${DB_URI:0:30}...)"
}

# ============================================================================
# MIGRATION COMMANDS
# ============================================================================

init_migrations() {
    echo "=== Initializing Migrations ==="
    cd "$PROJECT_ROOT"
    
    if [[ -d "migrations" ]]; then
        echo "⚠️  Migrations directory already exists"
        echo "   Skipping initialization"
        return 0
    fi
    
    export FLASK_APP=migrations_app.py
    flask db init
    
    echo "✅ Migrations initialized"
    echo "   Directory: $PROJECT_ROOT/migrations"
}

create_migration() {
    local name="$1"
    
    if [[ -z "$name" ]]; then
        echo "❌ Migration name required"
        echo "   Usage: $0 create <name>"
        exit 1
    fi
    
    echo "=== Creating Migration: $name ==="
    cd "$PROJECT_ROOT"
    
    if [[ ! -d "migrations" ]]; then
        echo "❌ Migrations not initialized"
        echo "   Run: $0 init"
        exit 1
    fi
    
    export FLASK_APP=migrations_app.py
    flask db migrate -m "$name"
    
    echo "✅ Migration created"
    echo "   Review the generated migration in migrations/versions/"
    echo "   Edit if needed, then run: $0 upgrade"
}

upgrade_migrations() {
    echo "=== Applying Migrations ==="
    cd "$PROJECT_ROOT"
    
    if [[ ! -d "migrations" ]]; then
        echo "❌ Migrations not initialized"
        echo "   Run: $0 init"
        exit 1
    fi
    
    export FLASK_APP=migrations_app.py
    flask db upgrade
    
    echo "✅ Migrations applied"
}

downgrade_migrations() {
    echo "=== Rolling Back Last Migration ==="
    cd "$PROJECT_ROOT"
    
    if [[ ! -d "migrations" ]]; then
        echo "❌ Migrations not initialized"
        exit 1
    fi
    
    export FLASK_APP=migrations_app.py
    flask db downgrade
    
    echo "✅ Migration rolled back"
}

show_current() {
    echo "=== Current Migration Version ==="
    cd "$PROJECT_ROOT"
    
    if [[ ! -d "migrations" ]]; then
        echo "❌ Migrations not initialized"
        exit 1
    fi
    
    export FLASK_APP=migrations_app.py
    flask db current
}

show_history() {
    echo "=== Migration History ==="
    cd "$PROJECT_ROOT"
    
    if [[ ! -d "migrations" ]]; then
        echo "❌ Migrations not initialized"
        exit 1
    fi
    
    export FLASK_APP=migrations_app.py
    flask db history
}

show_status() {
    echo "=== Migration Status ==="
    cd "$PROJECT_ROOT"
    
    if [[ ! -d "migrations" ]]; then
        echo "Migrations: Not initialized"
        echo "Run: $0 init"
        exit 0
    fi
    
    export FLASK_APP=migrations_app.py
    
    echo "Migrations directory: $PROJECT_ROOT/migrations"
    echo ""
    echo "Current version:"
    flask db current
    
    echo ""
    echo "Pending migrations:"
    # Check if there are pending migrations
    if flask db upgrade --sql 2>/dev/null | grep -q "CREATE\|ALTER\|DROP"; then
        echo "⚠️  Pending migrations found"
        echo "   Run: $0 upgrade"
    else
        echo "✅ No pending migrations"
    fi
}

# ============================================================================
# MAIN
# ============================================================================

if [[ $# -eq 0 ]]; then
    usage
fi

COMMAND="$1"
shift

check_database_uri

case "$COMMAND" in
    init)
        init_migrations
        ;;
    create)
        create_migration "$@"
        ;;
    upgrade)
        upgrade_migrations
        ;;
    downgrade)
        downgrade_migrations
        ;;
    current)
        show_current
        ;;
    history)
        show_history
        ;;
    status)
        show_status
        ;;
    *)
        echo "❌ Unknown command: $COMMAND"
        usage
        ;;
esac
