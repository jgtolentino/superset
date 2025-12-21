# CI Gate Requirements

## Mandatory Checks

All PRs MUST pass these gates before merge:

### 1. Smart Delta Validation

```yaml
# Reject custom modules without gap_level >= 2
- name: Check Smart Delta compliance
  run: |
    python scripts/validate_smart_delta.py
```

Rules:
- Custom module requires documented gap_level >= 2
- OCA alternative must not exist for gap_level 1
- External service requires ERP-unsafe justification

### 2. Security Validation

```yaml
- name: Security checks
  run: |
    # Check for ir.model.access.csv
    find custom_addons -name '__manifest__.py' -exec dirname {} \; | while read dir; do
      if [ ! -f "$dir/security/ir.model.access.csv" ]; then
        echo "ERROR: Missing security file in $dir"
        exit 1
      fi
    done
```

### 3. Schema Validation

```yaml
- name: Schema validation
  run: |
    # Ensure no raw SQL schema changes
    ! grep -r "CREATE TABLE\|ALTER TABLE\|DROP TABLE" custom_addons --include="*.py" \
      --exclude="*migration*"
```

### 4. OCA Reference Check

```yaml
- name: OCA reference validation
  run: |
    # Verify OCA modules in parity map exist
    python scripts/validate_oca_refs.py
```

### 5. Deterministic Output

```yaml
- name: Parity map hash
  run: |
    # Ensure same input produces same output
    sha256sum spec/smart-delta-engine/catalog/parity-map.json
```

### 6. Test Coverage

```yaml
- name: Run tests
  run: |
    odoo-bin -d test_db -i module_name --test-enable --stop-after-init
```

Minimum coverage: 80% for custom code

### 7. Linting

```yaml
- name: Lint
  run: |
    pylint custom_addons --rcfile=.pylintrc
    flake8 custom_addons
```

## Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/OCA/pylint-odoo
    rev: v9.0.0
    hooks:
      - id: pylint-odoo
  - repo: https://github.com/psf/black
    rev: 24.4.2
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
```

## Blocking vs Warning

| Check | Level |
|-------|-------|
| Missing security files | BLOCK |
| Custom without gap >= 2 | BLOCK |
| Missing OCA ref | BLOCK |
| Low test coverage | WARN |
| Linting issues | WARN |
