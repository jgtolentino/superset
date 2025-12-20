# Continue+ Task Checklist

> Implementation tasks with acceptance criteria

---

## M1: Foundation

### T1.1: Create Agent Command Files
- [x] Create `.claude/` directory
- [x] Create `.claude/commands/` directory
- [x] Write `plan.md` command
- [x] Write `implement.md` command
- [x] Write `verify.md` command
- [x] Write `ship.md` command

**Acceptance:** Commands appear in `/project:*` help

### T1.2: Configure Tool Allowlist
- [x] Create `.claude/settings.json`
- [x] Define safe git commands
- [x] Define safe verification commands
- [x] Define safe build commands

**Acceptance:** Non-allowlisted tools blocked

### T1.3: Documentation
- [x] Create `docs/skills-agent-guide.md`
- [ ] Add usage examples
- [ ] Document command outputs
- [ ] Add troubleshooting section

**Acceptance:** New users can onboard from docs

---

## M2: Verification Layer

### T2.1: Repo Health Script
- [ ] Create `scripts/repo_health.sh`
- [ ] Check CLAUDE.md exists
- [ ] Check .claude/ directory exists
- [ ] Check scripts/ directory exists
- [ ] Return meaningful exit codes

**Acceptance:** `./scripts/repo_health.sh` runs clean on valid repo

### T2.2: Verification Script
- [ ] Create `scripts/verify.sh`
- [ ] Call repo_health.sh
- [ ] Call spec_validate.sh
- [ ] Run lint if available
- [ ] Run typecheck if available
- [ ] Run tests if available

**Acceptance:** `./scripts/verify.sh` gates commits

### T2.3: Spec Validation Script
- [x] Create `scripts/spec_validate.sh`
- [x] Check spec/ directory exists
- [x] Find all spec bundles
- [x] Validate 4 required files
- [x] Check minimum content
- [x] Detect placeholders

**Acceptance:** CI uses script to block incomplete specs

### T2.4: Makefile Integration
- [ ] Add `make verify` target
- [ ] Add `make spec-validate` target
- [ ] Update help text

**Acceptance:** `make help` shows new targets

---

## M3: Spec Kit System

### T3.1: Spec Kit Template
- [x] Create continue-plus constitution.md
- [x] Create continue-plus prd.md
- [x] Create continue-plus plan.md
- [x] Create continue-plus tasks.md

**Acceptance:** Template passes validation

### T3.2: CI Enforcement Workflow
- [ ] Create `.github/workflows/spec-kit-enforce.yml`
- [ ] Run on pull_request
- [ ] Validate all spec bundles
- [ ] Check for placeholders
- [ ] Block merge if invalid

**Acceptance:** PRs blocked without valid spec kit

### T3.3: Documentation
- [ ] Document spec kit structure
- [ ] Provide examples
- [ ] Add to skills-agent-guide.md

**Acceptance:** Users can create new spec kits

---

## M4: CI-Aware Execution

### T4.1: Path-Based Rules
- [ ] Add paths-ignore to heavy workflows
- [ ] Exclude spec/**, .claude/**, docs/**
- [ ] Test with docs-only PR

**Acceptance:** Docs PRs don't trigger heavy CI

### T4.2: Agent Preflight Workflow
- [ ] Create preflight classification job
- [ ] Detect changed file categories
- [ ] Gate heavy jobs on classification
- [ ] Output classification result

**Acceptance:** Heavy jobs skip when not needed

### T4.3: Documentation
- [ ] Document CI patterns
- [ ] Provide workflow snippets
- [ ] Add troubleshooting guide

**Acceptance:** Teams can adopt patterns

---

## Completion Summary

| Milestone | Tasks | Completed | Remaining |
|-----------|-------|-----------|-----------|
| M1 | 3 | 3 | 0 |
| M2 | 4 | 1 | 3 |
| M3 | 3 | 1 | 2 |
| M4 | 3 | 0 | 3 |
| **Total** | 13 | 5 | 8 |

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-20 | Initial tasks |
