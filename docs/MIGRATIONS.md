# Database Migrations Guide

This guide explains how to manage database schema migrations for the Superset repository using Flask-Migrate.

## Overview

Database migrations allow you to:
- Version control your database schema
- Apply schema changes safely across environments
- Roll back changes if needed
- Collaborate on database changes with your team

## Prerequisites

### Environment Variables

Set the database connection string:

```bash
# In ~/.zshrc or .env
export SUPERSET__SQLALCHEMY_DATABASE_URI="postgresql+psycopg2://USER:PASS@HOST:PORT/DB"
# or
export SQLALCHEMY_DATABASE_URI="postgresql+psycopg2://USER:PASS@HOST:PORT/DB"
```

**Important**: Use PostgreSQL, not SQLite. SQLite is not suitable for production migrations.

### Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- psycopg2-binary

## Quick Start

### 1. Initialize Migrations (First Time Only)

```bash
./scripts/manage_migrations.sh init
```

This creates:
- `migrations/` directory
- `migrations/versions/` for migration scripts
- `migrations/alembic.ini` configuration file

### 2. Create a Migration

After modifying models in `migrations_app.py`:

```bash
./scripts/manage_migrations.sh create "add user preferences table"
```

This generates a migration script in `migrations/versions/` with:
- Timestamp prefix
- Descriptive name
- `upgrade()` function for applying changes
- `downgrade()` function for rolling back

### 3. Review the Migration

Open the generated file in `migrations/versions/` and review:
- Auto-detected schema changes
- Manual adjustments if needed
- Safety of operations

Example migration:

```python
def upgrade():
    # Create new table
    op.create_table(
        'user_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('theme', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    # Reverse the changes
    op.drop_table('user_preferences')
```

### 4. Apply Migrations

```bash
./scripts/manage_migrations.sh upgrade
```

This applies all pending migrations to the database.

### 5. Check Status

```bash
./scripts/manage_migrations.sh status
```

Shows:
- Current migration version
- Pending migrations
- Migration directory location

## Common Commands

### Show Current Version

```bash
./scripts/manage_migrations.sh current
```

### Show Migration History

```bash
./scripts/manage_migrations.sh history
```

### Roll Back Last Migration

```bash
./scripts/manage_migrations.sh downgrade
```

**Warning**: Only roll back if you understand the impact on your data.

## Adding Models

Edit `migrations_app.py` to add new models:

```python
class MyNewTable(db.Model):
    __tablename__ = 'my_new_table'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    def __repr__(self):
        return f'<MyNewTable {self.name}>'
```

Then create and apply migration:

```bash
./scripts/manage_migrations.sh create "add my_new_table"
./scripts/manage_migrations.sh upgrade
```

## CI/CD Integration

The repository includes automated migration testing in GitHub Actions:

```yaml
migration-test:
  runs-on: ubuntu-latest
  services:
    postgres:
      image: postgres:15
  steps:
    - name: Test migration initialization
      run: ./scripts/manage_migrations.sh init
    
    - name: Test migration creation
      run: ./scripts/manage_migrations.sh create "test migration"
    
    - name: Test migration apply
      run: ./scripts/manage_migrations.sh upgrade
```

## Best Practices

### 1. Always Review Generated Migrations

Flask-Migrate auto-detects changes but may miss:
- Data migrations
- Complex constraints
- Index optimizations

### 2. Test Migrations Before Production

```bash
# Test in development environment first
export SQLALCHEMY_DATABASE_URI="postgresql://localhost/superset_dev"
./scripts/manage_migrations.sh upgrade

# Then test in staging
export SQLALCHEMY_DATABASE_URI="postgresql://staging-host/superset_staging"
./scripts/manage_migrations.sh upgrade
```

### 3. Backup Before Migration

Always backup your database before applying migrations:

```bash
pg_dump -h HOST -U USER -d DATABASE > backup_$(date +%Y%m%d).sql
```

### 4. Use Descriptive Names

Good:
- `./scripts/manage_migrations.sh create "add user_preferences table"`
- `./scripts/manage_migrations.sh create "add email_verified column to users"`

Bad:
- `./scripts/manage_migrations.sh create "update database"`
- `./scripts/manage_migrations.sh create "changes"`

### 5. Keep Migrations Small

Create separate migrations for independent changes:
- One migration per logical schema change
- Easier to review and roll back
- Clearer history

### 6. Don't Edit Applied Migrations

Once a migration is applied and committed:
- Never edit it
- Create a new migration to fix issues
- Exception: If migration hasn't been shared with team

## Troubleshooting

### "Migrations not initialized"

```bash
./scripts/manage_migrations.sh init
```

### "Branch exists" Error

Multiple branches in migration history. Resolve with:

```bash
# Show history
./scripts/manage_migrations.sh history

# Merge branches
export FLASK_APP=migrations_app.py
flask db merge heads -m "merge branches"
```

### "Target database is not up to date"

Database has migrations not in your local directory:

```bash
# Pull latest migrations from version control
git pull

# Apply migrations
./scripts/manage_migrations.sh upgrade
```

### SQLite Error

```
❌ ERROR: SQLite not supported for migrations
   Use PostgreSQL for metadata database
```

Change your database URI to PostgreSQL:

```bash
export SUPERSET__SQLALCHEMY_DATABASE_URI="postgresql+psycopg2://HOST/DB"
```

## Migration Workflow

### Development

```
1. Make model changes in migrations_app.py
2. Create migration: ./scripts/manage_migrations.sh create "description"
3. Review generated migration
4. Test locally: ./scripts/manage_migrations.sh upgrade
5. Commit: git add migrations/ migrations_app.py && git commit
```

### Staging/Production

```
1. Pull latest code: git pull
2. Backup database: pg_dump ...
3. Apply migrations: ./scripts/manage_migrations.sh upgrade
4. Verify: ./scripts/manage_migrations.sh current
5. Test application
```

## Advanced Usage

### Generate SQL Without Applying

```bash
export FLASK_APP=migrations_app.py
flask db upgrade --sql > migration.sql
```

Review SQL before applying:

```bash
./scripts/manage_migrations.sh upgrade
```

### Stamp Database

Mark database as being at a specific version without running migrations:

```bash
export FLASK_APP=migrations_app.py
flask db stamp head
```

Use case: Existing database that needs migration tracking.

### Offline Mode

Generate migrations without database connection:

```bash
export FLASK_APP=migrations_app.py
flask db revision -m "manual migration" --autogenerate
```

## Resources

- [Flask-Migrate Documentation](https://flask-migrate.readthedocs.io/)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)

## Example: Complete Migration Cycle

```bash
# 1. Initialize (first time only)
./scripts/manage_migrations.sh init

# 2. Add model to migrations_app.py
cat >> migrations_app.py << 'EOF'

class BlogPost(db.Model):
    __tablename__ = 'blog_posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
EOF

# 3. Create migration
./scripts/manage_migrations.sh create "add blog_posts table"

# 4. Review migration
cat migrations/versions/*_add_blog_posts_table.py

# 5. Apply migration
./scripts/manage_migrations.sh upgrade

# 6. Check status
./scripts/manage_migrations.sh status

# Output:
# ✅ Current version: abc123 (add blog_posts table)
# ✅ No pending migrations
```

## Support

For issues or questions:
- Check troubleshooting section above
- Review Flask-Migrate documentation
- Open issue in repository
