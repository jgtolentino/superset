# Repository Verification Procedure

## Overview

This document defines the verification procedure for ensuring repository state is consistent with documentation and Smart Delta principles.

---

## Step 1 — Inventory

Scan and list:
- Odoo core modules used
- OCA repos + modules
- Custom modules (should be minimal)
- External services

```bash
# Example inventory command
find . -name "__manifest__.py" -exec grep -l "name" {} \;
```

---

## Step 2 — Cross-Check

For each module:
- Is it documented in docs/?
- Is install order documented?
- Is config vs code boundary clear?
- Is gap level assigned?

### Validation Matrix

| Check                     | Required | Location          |
|---------------------------|----------|-------------------|
| Module documented         | Yes      | docs/             |
| Install order defined     | Yes      | docs/ or manifest |
| Gap level assigned        | Yes      | parity map        |
| Smart Delta choice        | Yes      | parity map        |

---

## Step 3 — Conflict Scan

Check for conflicts between:
- docs vs Odoo 18 official behavior
- docs vs OCA module behavior
- docs vs repo code/config
- docs vs n8n workflows
- docs vs CI rules

### Conflict Resolution Priority

1. This repo's docs/ (highest authority)
2. Odoo 18 official docs
3. OCA README / manifests
4. Enterprise reference docs
5. Code comments (lowest authority)

---

## Step 4 — Resolution

Apply Smart Delta resolution order:

1. **Config** — Can this be done with Odoo settings?
2. **OCA** — Does OCA have a module for this?
3. **Minimal Custom** — Is custom code reusable?
4. **External** — Is the operation ERP-unsafe?

Document deviations explicitly using conflict annotation format.

---

## Step 5 — Update Docs

After resolution:
- Update or add missing sections
- Add conflict notes where needed
- Update Smart Delta classification
- Update gap levels if changed
- Regenerate parity map

---

## Compliance Status

Repository is **NOT compliant** until all steps pass:

- [ ] Step 1: Inventory complete
- [ ] Step 2: All modules cross-checked
- [ ] Step 3: No unresolved conflicts
- [ ] Step 4: All gaps resolved per Smart Delta
- [ ] Step 5: Docs updated

---

## Agent / CI Verification Prompt

Use this prompt for automated verification:

```text
Scan the repository.

1. Identify missing or incomplete documentation under docs/.
2. Detect conflicts between:
   - docs vs Odoo 18 official behavior
   - docs vs OCA module behavior
   - docs vs repo code/config
3. For each conflict:
   - Describe the conflict
   - Recommend the authoritative source
   - Propose a doc update
4. Output:
   - A list of missing docs
   - A list of conflicts
   - Exact markdown patches to apply

Do NOT modify code. Documentation only.
```

---

## Automated Checks

### CI Gates

| Check                        | Enforcement |
|------------------------------|-------------|
| docs/ has required sections  | Block merge |
| New modules are documented   | Block merge |
| Custom modules have gap >= 2 | Block merge |
| Parity map is up to date     | Block merge |

### Advisory Checks

| Check                        | Enforcement |
|------------------------------|-------------|
| Docs modified > 30 days ago  | Warning     |
| OCA modules not verified     | Warning     |
| Missing implementation notes | Warning     |
