# Quick Reference: Dashboard Import & Migrations

Quick reference for dashboard import and database migration features.

## Dashboard Import

### Quick Start

```bash
# Set environment
export BASE_URL="https://superset.example.com"
export SUPERSET_ADMIN_USER="admin"
export SUPERSET_ADMIN_PASS="password"

# Import all dashboards
make import-dashboards

# Import single dashboard
make import-dashboard DASH=examples/dashboards/sample_dashboard.json
```

### Command Line

```bash
# Help
./scripts/import_dashboard.py --help

# Import file
./scripts/import_dashboard.py path/to/dashboard.json

# Import directory
./scripts/import_dashboard.py path/to/dashboards/

# Skip auth check (faster, but risky)
./scripts/import_dashboard.py --skip-auth-check dashboards/
```

### Exit Codes

- `0` - Success
- `1` - Import failed
- `2` - Missing environment variables

## Database Migrations

### Quick Start

```bash
# Set environment
export SQLALCHEMY_DATABASE_URI="postgresql://host/db"

# Initialize (first time)
make migration-init

# Create migration
make migration-create MSG="add user table"

# Apply migrations
make migration-upgrade

# Check status
make migration-status
```

### Command Line

```bash
# Help
./scripts/manage_migrations.sh

# Initialize
./scripts/manage_migrations.sh init

# Create migration
./scripts/manage_migrations.sh create "migration description"

# Apply all pending
./scripts/manage_migrations.sh upgrade

# Show current version
./scripts/manage_migrations.sh current

# Show history
./scripts/manage_migrations.sh history

# Show status
./scripts/manage_migrations.sh status

# Rollback (dangerous!)
./scripts/manage_migrations.sh downgrade
```

## Environment Variables

### Dashboard Import

```bash
BASE_URL                    # Required: Superset URL
SUPERSET_ADMIN_USER         # Required: Admin username
SUPERSET_ADMIN_PASS         # Required: Admin password
```

### Migrations

```bash
SUPERSET__SQLALCHEMY_DATABASE_URI    # Preferred
# or
SQLALCHEMY_DATABASE_URI              # Fallback
```

## Common Tasks

### Export Dashboard from Superset

1. Navigate to dashboard in Superset UI
2. Click ⋮ menu → Export
3. Save ZIP file
4. Extract JSON from ZIP
5. Place in `examples/dashboards/`

### Create New Migration

1. Edit `migrations_app.py` to add model:
   ```python
   class MyTable(db.Model):
       __tablename__ = 'my_table'
       id = db.Column(db.Integer, primary_key=True)
       name = db.Column(db.String(255))
   ```

2. Create migration:
   ```bash
   make migration-create MSG="add my_table"
   ```

3. Review generated file in `migrations/versions/`

4. Apply migration:
   ```bash
   make migration-upgrade
   ```

### CI/CD Integration

GitHub Actions automatically runs:
- Script validation (every push)
- Migration tests (with PostgreSQL)
- Dashboard import tests (when secrets available)

### Troubleshooting

**"BLOCKED: missing env var"**
```bash
# Check which vars are set
env | grep -E "BASE_URL|SUPERSET_|SQLALCHEMY"

# Set missing vars in ~/.zshrc
export SUPERSET_ADMIN_USER="your_username"
source ~/.zshrc
```

**"Authentication failed"**
```bash
# Verify credentials
echo "User: $SUPERSET_ADMIN_USER"
echo "Pass length: ${#SUPERSET_ADMIN_PASS}"

# Test login manually
curl -X POST "$BASE_URL/api/v1/security/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$SUPERSET_ADMIN_USER\",\"password\":\"$SUPERSET_ADMIN_PASS\",\"provider\":\"db\"}"
```

**"Migrations not initialized"**
```bash
make migration-init
```

**"SQLite not supported"**
```bash
# Use PostgreSQL instead
export SQLALCHEMY_DATABASE_URI="postgresql://host/db"
```

## Documentation

- **Dashboard Import:** [docs/DASHBOARD_IMPORT.md](DASHBOARD_IMPORT.md)
- **Migrations:** [docs/MIGRATIONS.md](MIGRATIONS.md)
- **n8n Integration:** [docs/N8N_INTEGRATION.md](N8N_INTEGRATION.md)
- **Implementation:** [docs/IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)

## Makefile Targets

```bash
make help                    # Show all targets

# Dashboard
make import-dashboards       # Import all from examples/dashboards/
make import-dashboard        # Import single (DASH=file.json)

# Migrations
make migration-init         # Initialize migrations
make migration-create       # Create migration (MSG="description")
make migration-upgrade      # Apply all pending
make migration-status       # Show status
make migration-history      # Show history
make migration-downgrade    # Rollback last (dangerous!)
```

## Examples

### Dashboard Import Workflow

```bash
# Development
export BASE_URL="http://localhost:8088"
./scripts/import_dashboard.py examples/dashboards/

# Staging
export BASE_URL="https://staging.superset.example.com"
./scripts/import_dashboard.py examples/dashboards/

# Production
export BASE_URL="https://superset.example.com"
./scripts/import_dashboard.py examples/dashboards/production/
```

### Migration Workflow

```bash
# Development
export SQLALCHEMY_DATABASE_URI="postgresql://localhost/superset_dev"
make migration-upgrade

# Staging
export SQLALCHEMY_DATABASE_URI="postgresql://staging/superset"
make migration-upgrade

# Production (with backup!)
pg_dump superset > backup_$(date +%Y%m%d).sql
export SQLALCHEMY_DATABASE_URI="postgresql://prod/superset"
make migration-upgrade
```

## Tips

1. **Always backup database before migrations**
2. **Test in dev/staging first**
3. **Use descriptive migration names**
4. **Keep dashboards in version control**
5. **Validate JSON before import**
6. **Review generated migrations**
7. **Never edit applied migrations**

## Support

- Repository: https://github.com/jgtolentino/superset
- Issues: https://github.com/jgtolentino/superset/issues
- Documentation: [docs/](../docs/)
