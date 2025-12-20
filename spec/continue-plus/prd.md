# Continue+ Product Requirements Document

> Product requirements for the docs-to-code agentic development system

## 1. Product Summary

Continue+ is an improved "docs-to-code" agentic development platform built on top of Claude Code's IDE-native workflow, adding:

- **Spec Kit enforcement** - structured documentation as executable intent
- **Deterministic multi-agent orchestration** - plan/implement/verify/ship roles
- **CI-aware execution** - intelligent pipeline triggering based on change type

The system ensures agent-generated work reliably ships in repos with heavy CI without noisy failures.

---

## 2. Problem Statement

Teams using IDE agents frequently hit predictable failure modes:

### CI Mismatch
- Agent makes non-code changes (docs, specs, infra)
- Heavy CI pipelines trigger anyway (e.g., OCA matrix, full test suite)
- PRs go red, slowing merges and lowering trust

### Non-Deterministic Behavior
- "Agent" behavior varies by prompt/ruleset
- Hard to reproduce or audit what happened
- No standard for what agents should do

### No Execution Contract
- Planning, implementation, verification are mixed
- Output is not reliably review-ready
- Unclear what was done and why

### No Repo-Standard Governance
- Rules live in inconsistent formats
- Missing enforcement that specs exist and are complete
- Tribal knowledge instead of documented process

---

## 3. Goals

1. Make "docs-to-code" **repeatable and mergeable**
2. Enforce a **single execution contract** across repos
3. Keep the experience **IDE-native and fast**
4. **Reduce CI noise** by making agents CI-aware
5. Produce **PR-ready outputs** with evidence

---

## 4. Non-Goals

- Autonomous long-running agents
- Replacing CI systems or Git providers
- Hosting proprietary model infrastructure
- Full SCM management (Continue+ integrates; it doesn't replace GitHub/GitLab)

---

## 5. Target Users

### Primary Users

| Persona | Description | Key Needs |
|---------|-------------|-----------|
| Solo Founders | Shipping fast with IDE agents | Speed, reliability |
| Platform/DevEx Teams | Standardizing agent behavior | Governance, consistency |
| Heavy-CI Teams | Monorepos, OCA/Odoo, regulated | CI efficiency, compliance |

### User Characteristics

- Comfortable with CLI and IDE tooling
- Using Claude Code, Codex, or similar agents
- Have existing CI/CD pipelines
- Want agent work to be reviewable

---

## 6. Core User Stories

### US-1: Planning
> As a developer, I want to run `/plan` and get a file-level change plan without any edits, so I can review before implementation.

**Acceptance Criteria:**
- Plan shows scope, files to change, risks
- No files are modified
- Plan is copy-paste ready for spec/tasks.md

### US-2: Implementation
> As a developer, I want `/implement` to execute only the plan with minimal diffs, so changes are easy to review.

**Acceptance Criteria:**
- Only planned files are modified
- Changes are minimal
- Deviations from plan are documented

### US-3: Verification
> As a developer, I want `/verify` to run checks and fix failures automatically, so I get a green build.

**Acceptance Criteria:**
- Standard verification commands run
- Failures are fixed and rerun
- Final status is clearly reported

### US-4: PR-Ready Output
> As a reviewer, I want PR summaries that include what changed, why, and verification evidence, so I can review efficiently.

**Acceptance Criteria:**
- Summary explains intent
- Evidence shows verification ran
- Risks and rollback documented

### US-5: Spec Enforcement
> As a platform owner, I want Spec Kit enforcement so every repo has constitution/prd/plan/tasks and no placeholders.

**Acceptance Criteria:**
- CI blocks if spec kit incomplete
- Placeholders are detected and rejected
- Minimum content requirements enforced

### US-6: CI-Aware Changes
> As a CI owner, I want agent changes to skip irrelevant pipelines when only docs/spec/agent config changed.

**Acceptance Criteria:**
- Docs-only changes skip heavy CI
- Code changes trigger appropriate pipelines
- Path-based rules are respected

---

## 7. Requirements

### 7.1 Spec Kit Enforcement

| ID | Requirement | Priority |
|----|-------------|----------|
| R1.1 | Detect `spec/<slug>/{constitution,prd,plan,tasks}.md` | Must |
| R1.2 | Block "ship" if spec kit incomplete | Must |
| R1.3 | Flag placeholders (TODO/TBD/LOREM) | Must |
| R1.4 | Enforce minimum content per file | Should |
| R1.5 | Link PRs to spec slug and tasks | Should |

### 7.2 Multi-Agent Orchestration

| ID | Requirement | Priority |
|----|-------------|----------|
| R2.1 | Provide Planner role (no edits) | Must |
| R2.2 | Provide Implementer role (edits only) | Must |
| R2.3 | Provide Verifier role (runs checks) | Must |
| R2.4 | Provide Ship orchestrator | Must |
| R2.5 | Stable output format per command | Must |
| R2.6 | Outputs written to repo docs or PR | Should |

### 7.3 CI-Aware Execution

| ID | Requirement | Priority |
|----|-------------|----------|
| R3.1 | Classify changed files by category | Must |
| R3.2 | Recommend CI short-circuit for docs-only | Must |
| R3.3 | Provide drop-in workflow snippets | Should |
| R3.4 | Enforce repo CI policy during /ship | Should |

### 7.4 PR-Grade Outputs

| ID | Requirement | Priority |
|----|-------------|----------|
| R4.1 | Verification evidence in output | Must |
| R4.2 | Minimal diffs enforced | Must |
| R4.3 | Tool allowlist respected | Must |
| R4.4 | Commit message explains why | Should |

---

## 8. Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|-------------------|
| Task completion rate | > 90% | Tasks done without follow-ups |
| PR acceptance rate | > 85% | PRs merged without major changes |
| CI false positive reduction | > 70% | Fewer red PRs from docs changes |
| Verification compliance | 100% | Commits with evidence |
| User satisfaction | > 4/5 | Survey feedback |

---

## 9. Out of Scope (Future)

- Visual workflow builder
- Cross-repo agent coordination
- Real-time collaboration
- Custom model training
- Enterprise SSO integration

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-20 | Initial PRD |
