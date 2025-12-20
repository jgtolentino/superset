# Continue+ Constitution

> Governing principles for the docs-to-code agentic development system

## Purpose

Continue+ is an improved "docs-to-code" agentic development platform that uses documentation as the primary execution interface for AI coding agents. Specs are not descriptive - they are **executable intent**.

---

## Core Principles

### 1. Documentation as Execution Interface

**Specs drive code, not prompts.**

- CLAUDE.md is authoritative runtime context
- Spec Kits define what agents can and must do
- Changes to behavior require changes to docs
- Prompts are ephemeral; docs are persistent

### 2. Deterministic Workflow Contract

**Every agent session follows the same contract.**

```
explore → plan → implement → verify → commit
```

- No skipping steps
- No hidden reasoning
- No silent behavior changes
- Outputs are auditable

### 3. Role Separation

**Agents have distinct, non-overlapping responsibilities.**

| Role | Allowed | Forbidden |
|------|---------|-----------|
| Planner | Read, explore, output plan | Edit files, run commands |
| Implementer | Edit files per plan | Run tests, add features |
| Verifier | Run checks, fix failures | Add features, refactor |
| Orchestrator | Coordinate all roles | Skip steps, bypass checks |

### 4. Minimal Intervention

**Make the smallest change that satisfies the requirement.**

- Prefer editing over creating
- No speculative improvements
- No refactoring unrelated code
- No adding "while we're here" features

### 5. Evidence-Based Verification

**All claims must be backed by evidence.**

- "Tests pass" requires showing test output
- "Build succeeds" requires showing build output
- No assumed success
- No hidden failures

### 6. CI-Aware Execution

**Agents must understand CI implications.**

- Docs-only changes skip heavy pipelines
- Code changes trigger appropriate tests
- Agents respect path-based CI rules
- No breaking existing workflows

---

## Non-Negotiables

### 1. Spec Kit Required for Complex Skills

```yaml
rule: spec_kit_required
description: Skills with >3 scripts must have spec kit
enforcement: hard_block
rationale: Complex skills need documented intent
```

### 2. No Placeholders in Specs

```yaml
rule: no_placeholders
description: TODO/TBD/LOREM blocked by CI
enforcement: hard_block
rationale: Specs are executable, not drafts
```

### 3. Verification Before Commit

```yaml
rule: verify_first
description: All mutations must end with verification
enforcement: hard_requirement
rationale: Broken code must not be committed
```

### 4. Allowlist Enforcement

```yaml
rule: respect_allowlist
description: Only use tools in .claude/settings.json
enforcement: hard_block
rationale: Security and predictability
```

### 5. Minimal Diffs

```yaml
rule: minimal_diffs
description: Smallest change that satisfies requirement
enforcement: advisory
rationale: Easier review, fewer bugs
```

---

## Scope Definition

### In Scope

Operations where Continue+ provides value:

| Operation | Traditional | Continue+ |
|-----------|-------------|-----------|
| Feature implementation | Prompt → code | Spec → plan → code |
| Bug fixes | Debug → patch | Analyze → plan → patch → verify |
| Refactoring | Edit → hope | Plan → edit → verify → commit |
| Documentation | Write docs | Update docs with code |

### Out of Scope

Operations where Continue+ is not needed:

| Operation | Reason |
|-----------|--------|
| Single-line fixes | Too simple for orchestration |
| Exploratory coding | Need flexibility, not structure |
| Learning/experimentation | Overhead not justified |
| Emergency hotfixes | Speed trumps process |

---

## Decision Matrix

### When to Use Full Workflow

```
IF change requires multiple files:
    USE full workflow (plan → implement → verify)

IF change affects public API:
    USE full workflow with extra review

IF change is speculative:
    USE plan-only first, get approval
```

### When to Use Simplified Flow

```
IF change is single file, isolated:
    USE implement → verify (skip plan)

IF change is documentation only:
    USE implement only (skip verify)

IF change is configuration:
    USE implement → verify
```

---

## Enforcement Levels

### Level 1: Advisory (Default)

- Show recommendations
- Log decisions
- Allow override

### Level 2: Warning

- Display warning before bypass
- Require acknowledgment
- Log for audit

### Level 3: Strict (Opt-in)

- Block non-compliant actions
- Require explicit override
- Full audit trail

---

## Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Agent task completion | > 90% | Tasks completed without follow-ups |
| PR acceptance rate | > 85% | PRs merged without major revisions |
| CI noise reduction | > 70% | Fewer false-positive CI failures |
| Verification compliance | 100% | All commits have verification evidence |
| Spec coverage | > 80% | Skills with spec kits |

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-20 | Initial constitution |
