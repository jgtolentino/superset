# Migrations as Source of Truth

## Core Principle

**Odoo module manifests and migrations are the single source of truth for database schema.**

## Rules

### Schema Changes

1. All schema changes MUST be made via Odoo module definitions
2. Model fields define the schema, not raw SQL
3. Use `_sql_constraints` for database-level constraints
4. Pre/post migration hooks for data transformations

### Migration Script Structure

```python
# migrations/18.0.1.0.1/pre-migration.py
def migrate(cr, version):
    """Pre-migration: runs before module update."""
    if not version:
        return
    # Schema preparation here

# migrations/18.0.1.0.1/post-migration.py
def migrate(cr, version):
    """Post-migration: runs after module update."""
    if not version:
        return
    # Data migration here
```

### External Databases (Supabase)

When syncing to external databases:

1. **Read-only replication** - Never write back to Odoo
2. **Schema derived from Odoo** - Generate DDL from Odoo models
3. **RLS policies** - Mirror Odoo record rules

### Version Numbering

Format: `<odoo_version>.<major>.<minor>.<patch>`

Example: `18.0.1.2.3`
- `18.0` - Odoo version
- `1` - Major (breaking changes)
- `2` - Minor (new features)
- `3` - Patch (bug fixes)

## CI Validation

Before merge:

- [ ] No raw SQL schema changes outside migrations
- [ ] Migration scripts are idempotent
- [ ] Version number incremented
- [ ] Tests pass with fresh install AND upgrade
