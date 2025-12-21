# Docs Governance & Verification

This repository treats documentation as **source-of-truth artifacts**.
Code, configs, and automations MUST reconcile with docs, not override them.

## 1. Doc Coverage Rules

Every functional area MUST have:
- Purpose & scope
- Module list (core + OCA)
- Install order
- Config-only vs custom boundaries
- Automation hooks (n8n / CI)
- Known gaps & Smart Delta choice

### Required Sections (minimum)
- Finance
- PPM / Projects
- HR
- Approvals & Workflows
- Analytics / BI
- Integrations
- Security & RLS
- Automation (n8n, CI)

Missing any section = invalid state.

---

## 2. Canonical Source Rule

If information conflicts, resolve using this priority:

1. **This repo's docs/**
2. Odoo 18 official docs
3. OCA README / manifests
4. Enterprise reference docs (SAP, etc.)
5. Code comments (lowest authority)

Conflicts MUST be documented, not silently fixed.

---

## 3. Conflict Annotation Standard

When conflicts exist, annotate explicitly:

```md
> Conflict Note
> Source A: Odoo Docs say X
> Source B: OCA module enforces Y
> Resolution: Adopt Y (OCA), document deviation
```

No silent divergence allowed.

---

## 4. Verification Checklist (MANDATORY)

Before merging ANY change:

- [ ] All modules referenced in docs exist or are linked
- [ ] No undocumented custom modules
- [ ] OCA modules include repo + module name
- [ ] Install order is deterministic
- [ ] Smart Delta choice is explicit
- [ ] Conflicts annotated (if any)
- [ ] BI / analytics marked read-only if external

---

## 5. Docs Drift Detection

Docs are considered **stale** if:

* A module is added without doc reference
* An OCA dependency changes
* Config behavior diverges from docs

Required action:

* Update docs FIRST
* Then update code/config

---

## 6. Enforcement

CI SHOULD fail if:

* `docs/` missing required sections
* New modules lack documentation
* Custom modules violate Smart Delta rules
