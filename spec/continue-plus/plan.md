# Continue+ Implementation Plan

> Technical architecture and implementation roadmap

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Continue+ System                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                        Agent Layer                                   │   │
│   │  ┌──────────┐  ┌──────────────┐  ┌──────────┐  ┌──────────┐        │   │
│   │  │ Planner  │  │ Implementer  │  │ Verifier │  │   Ship   │        │   │
│   │  └────┬─────┘  └──────┬───────┘  └────┬─────┘  └────┬─────┘        │   │
│   │       │               │               │              │              │   │
│   └───────┼───────────────┼───────────────┼──────────────┼──────────────┘   │
│           │               │               │              │                   │
│           ▼               ▼               ▼              ▼                   │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                     Execution Layer                                  │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐       │   │
│   │  │  Spec Kit    │  │   Tool       │  │    Verification      │       │   │
│   │  │  Validator   │  │  Allowlist   │  │    Gate              │       │   │
│   │  └──────────────┘  └──────────────┘  └──────────────────────┘       │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                     Integration Layer                                │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐       │   │
│   │  │  CLAUDE.md   │  │   CI/CD      │  │    Git Operations    │       │   │
│   │  │  Loader      │  │   Hooks      │  │    (commit, push)    │       │   │
│   │  └──────────────┘  └──────────────┘  └──────────────────────┘       │   │
│   └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Design

### 1. Agent Commands

**Location:** `.claude/commands/`

Each command is a markdown file that defines:
- Role and purpose
- Input handling
- Rules and constraints
- Required output format

**Files:**
- `plan.md` - Planner agent
- `implement.md` - Implementer agent
- `verify.md` - Verifier agent
- `ship.md` - Orchestrator agent

### 2. Spec Kit Validator

**Location:** `scripts/spec_validate.sh`

**Responsibilities:**
- Check spec directory structure exists
- Validate all 4 required files present
- Check minimum content (10+ non-empty lines)
- Detect placeholders (TODO/TBD/LOREM)

**Implementation:**
```bash
#!/usr/bin/env bash
set -euo pipefail

fail=0

# Find all spec bundles
while IFS= read -r cfile; do
  slug_dir="$(dirname "$cfile")"
  for f in constitution.md prd.md plan.md tasks.md; do
    path="$slug_dir/$f"
    # Check existence
    # Check content length
    # Check for placeholders
  done
done < <(find spec -name constitution.md)

exit "$fail"
```

### 3. Tool Allowlist

**Location:** `.claude/settings.json`

**Structure:**
```json
{
  "allowedTools": [
    "Edit",
    "Bash(git status)",
    "Bash(./scripts/verify.sh)",
    ...
  ]
}
```

**Enforcement:**
- Claude Code reads this on session start
- Non-allowlisted tools are blocked
- Explicit patterns for safe commands

### 4. Verification Gate

**Location:** `scripts/verify.sh`

**Responsibilities:**
- Run repo health check
- Run spec validation
- Run linting
- Run type checking
- Run tests

**Flow:**
```
repo_health.sh → spec_validate.sh → lint → typecheck → test
```

### 5. CI Workflows

**Location:** `.github/workflows/`

**Files:**
- `spec-kit-enforce.yml` - Validate spec kits on PR
- `verify-gates.yml` - Run verification scripts

---

## Implementation Milestones

### M1: Foundation (Week 1)

**Deliverables:**
- Agent command files (plan, implement, verify, ship)
- Settings.json with allowlist
- Basic documentation

**Tasks:**
1. Create `.claude/` directory structure
2. Write command markdown files
3. Define initial allowlist
4. Document usage in README

**Exit Criteria:**
- [ ] Commands available via `/project:*`
- [ ] Allowlist blocks unauthorized tools
- [ ] Documentation complete

### M2: Verification Layer (Week 2)

**Deliverables:**
- `scripts/repo_health.sh`
- `scripts/verify.sh`
- `scripts/spec_validate.sh`

**Tasks:**
1. Implement repo health checks
2. Implement verification script
3. Implement spec validation
4. Add to Makefile

**Exit Criteria:**
- [ ] `make verify` works
- [ ] Scripts detect common issues
- [ ] Exit codes are meaningful

### M3: Spec Kit System (Week 3)

**Deliverables:**
- Spec kit template
- Validation CI workflow
- Documentation

**Tasks:**
1. Create spec kit template
2. Implement CI workflow
3. Document spec kit structure
4. Add enforcement rules

**Exit Criteria:**
- [ ] CI blocks incomplete spec kits
- [ ] Placeholders detected
- [ ] Template is usable

### M4: CI-Aware Execution (Week 4)

**Deliverables:**
- Path-based CI rules
- Agent-preflight workflow
- Documentation

**Tasks:**
1. Add paths-ignore to heavy workflows
2. Create preflight classification job
3. Document CI patterns
4. Test with real PRs

**Exit Criteria:**
- [ ] Docs-only PRs skip heavy CI
- [ ] Code PRs trigger appropriate tests
- [ ] False positives reduced

---

## Technical Specifications

### Command Output Format

Each command produces structured output:

**Planner:**
```markdown
## Scope
<description>

## Files
- path/file.py (action) - description

## Risks
- risk 1
- risk 2

## Verification
```bash
<commands>
```

## Tasks
- [ ] task 1
- [ ] task 2
```

**Verifier:**
```markdown
## Verification Run
Command: <cmd>
Status: PASS/FAIL

## Issues
1. <issue>
   - Cause: <cause>
   - Fix: <fix>

## Final Status
Status: PASS/FAIL
```

### Spec Kit Schema

```yaml
spec/<slug>/
  constitution.md:
    required_sections:
      - Purpose
      - Core Principles
      - Non-Negotiables
      - Scope Definition
    min_lines: 50

  prd.md:
    required_sections:
      - Problem Statement
      - Goals
      - User Stories
      - Requirements
    min_lines: 40

  plan.md:
    required_sections:
      - Architecture
      - Components
      - Milestones
    min_lines: 30

  tasks.md:
    required_sections:
      - Task list with checkboxes
    min_lines: 10
```

---

## Risk Mitigation

| Risk | Mitigation | Owner |
|------|------------|-------|
| Agents bypass rules | Strict allowlist | Platform |
| Specs become stale | CI enforcement | DevEx |
| False CI positives | Path-based rules | CI Owner |
| Adoption friction | Good defaults | Product |

---

## Dependencies

### Internal
- Claude Code CLI
- Existing skills framework
- CI/CD infrastructure

### External
- GitHub Actions
- Git
- Shell environment

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-12-20 | Initial plan |
