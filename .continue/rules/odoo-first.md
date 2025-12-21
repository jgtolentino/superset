# Odoo-First Development Rules

## Smart Delta Hierarchy

When implementing any feature, follow this strict priority order:

1. **Config** - Can this be done with native Odoo settings? Use it.
2. **OCA** - Does OCA have a module? Install it instead of writing code.
3. **Minimal Custom** - Only if reusable and gap_level >= 2.
4. **External** - Only for ERP-unsafe operations (analytics, ML, heavy compute).

## Code Generation Rules

### NEVER

- Create custom modules when OCA alternatives exist
- Add controllers or routes unless absolutely necessary
- Write JavaScript unless required for UX
- Bypass Odoo ORM with raw SQL
- Create circular dependencies between modules

### ALWAYS

- Check OCA repositories first: https://github.com/OCA
- Use `_inherit` over `_name` for extending models
- Follow Odoo module naming conventions: `<category>_<feature>`
- Include proper security rules (ir.model.access.csv)
- Write tests for custom code

### Module Structure

```
custom_addons/
└── module_name/
    ├── __manifest__.py
    ├── __init__.py
    ├── models/
    │   ├── __init__.py
    │   └── model_name.py
    ├── views/
    │   └── model_name_views.xml
    ├── security/
    │   ├── ir.model.access.csv
    │   └── security.xml
    └── data/
        └── data.xml
```

### Manifest Requirements

```python
{
    'name': 'Module Name',
    'version': '18.0.1.0.0',
    'category': 'Category',
    'license': 'AGPL-3',
    'depends': ['base'],  # Minimal dependencies
    'data': [],
    'installable': True,
    'auto_install': False,
}
```

## RLS Requirements

Every custom model MUST have:

1. `ir.model.access.csv` with group-based permissions
2. Record rules for multi-company isolation (if applicable)
3. Field-level access controls for sensitive data

## Migration as Source of Truth

- Database schema changes ONLY via Odoo migrations
- Never modify Supabase/external DB schemas directly
- Use Odoo's upgrade scripts for data migrations
