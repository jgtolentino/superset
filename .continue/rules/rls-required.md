# Row-Level Security (RLS) Requirements

## Odoo Security Model

Every custom model MUST implement proper access controls.

### Access Control Checklist

1. **Model Access Rights** (`ir.model.access.csv`)
2. **Record Rules** (`ir.rule` for row-level filtering)
3. **Field Groups** (field-level access via `groups` attribute)
4. **Menu Access** (menu visibility via security groups)

### ir.model.access.csv Template

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_model_user,model.name user,model_model_name,base.group_user,1,0,0,0
access_model_manager,model.name manager,model_model_name,module.group_manager,1,1,1,1
```

### Record Rules (Multi-Company)

```xml
<record id="rule_model_company" model="ir.rule">
    <field name="name">Model: multi-company</field>
    <field name="model_id" ref="model_model_name"/>
    <field name="domain_force">[
        '|',
        ('company_id', '=', False),
        ('company_id', 'in', company_ids)
    ]</field>
</record>
```

### Supabase RLS Equivalent

When replicating to Supabase, create matching RLS policies:

```sql
-- Enable RLS
ALTER TABLE public.table_name ENABLE ROW LEVEL SECURITY;

-- Multi-tenant isolation
CREATE POLICY "tenant_isolation" ON public.table_name
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant')::uuid);

-- Read-only for analytics
CREATE POLICY "analytics_read_only" ON analytics.odoo_mirror
    FOR SELECT
    USING (true);
```

## Sensitive Data

Fields containing sensitive data MUST:

1. Use `groups` attribute to restrict access
2. Be excluded from API exports unless explicitly allowed
3. Be masked in logs and error messages

```python
class Model(models.Model):
    _name = 'model.name'

    sensitive_field = fields.Char(groups='base.group_system')
    salary = fields.Monetary(groups='hr.group_hr_manager')
```
