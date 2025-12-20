# Skills Agent System - Complete Guide

> Comprehensive documentation for the docs-to-code agentic development system

## Overview

This repository implements a **lightweight, bash-based skills framework** for Claude Code and other AI coding agents. The system uses documentation as the primary execution interface - specs are not descriptive, they are **executable intent**.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         Skills Agent Framework                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌────────────────────┐         ┌────────────────────────────────┐         │
│   │  skills/           │         │  spec/                          │         │
│   │  (Implementations) │◀───────▶│  (Knowledge Base / Spec Kits)   │         │
│   └─────────┬──────────┘         └────────────────────────────────┘         │
│             │                                                                │
│             ▼                                                                │
│   ┌────────────────────┐         ┌────────────────────────────────┐         │
│   │  Makefile          │         │  .github/workflows/             │         │
│   │  (Binding Layer)   │◀───────▶│  (CI/CD Automation)             │         │
│   └────────────────────┘         └────────────────────────────────┘         │
│             │                                                                │
│             ▼                                                                │
│   ┌────────────────────┐         ┌────────────────────────────────┐         │
│   │  .claude/          │         │  CLAUDE.md                      │         │
│   │  (Agent Config)    │◀───────▶│  (Runtime Context)              │         │
│   └────────────────────┘         └────────────────────────────────┘         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Skills Definitions

### Current Skills

| Skill | Status | Purpose |
|-------|--------|---------|
| `docker-image-build` | **Implemented** | Multi-arch Docker builds, scanning, push |
| `mcp-tool-enforcer` | **Spec Only** | Policy enforcement for optimal tool selection |

### Skill Directory Structure

```
skills/
├── docker-image-build/
│   ├── README.md              # Usage documentation
│   └── scripts/
│       ├── common.sh          # Shared utilities (sourced by all scripts)
│       ├── build.sh           # Build multi-arch images
│       ├── scan.sh            # Security vulnerability scanning
│       ├── push.sh            # Push to container registry
│       └── verify.sh          # Verify image integrity
│
└── mcp-tool-enforcer/
    └── README.md              # Links to spec documents
```

### Creating a New Skill

1. Create directory: `skills/<skill-name>/`
2. Add `README.md` with usage documentation
3. Add `scripts/` directory with executable scripts
4. Source `common.sh` for shared utilities
5. Register in `Makefile` with targets
6. (Optional) Create spec kit in `spec/<skill-name>/`

---

## 2. Binding Layer

Skills are **bound** through three mechanisms:

### A. Makefile Targets

```makefile
# Direct invocation with environment passthrough
image-build: ## Build multi-arch Docker image
    @IMAGE_REPO=$(IMAGE_REPO) IMAGE_TAG=$(IMAGE_TAG) \
        ./skills/docker-image-build/scripts/build.sh $(ARGS)
```

**Pattern:** `make <target>` → `./skills/<skill>/scripts/<script>.sh`

### B. GitHub Actions Workflows

```yaml
on:
  push:
    branches: [main]
    paths:
      - 'skills/docker-image-build/**'
      - 'Dockerfile'
```

### C. Common Utilities (`common.sh`)

Every skill script sources shared utilities:

```bash
#!/usr/bin/env bash
source "$(dirname "$0")/common.sh"
```

**Provided Functions:**

| Function | Purpose |
|----------|---------|
| `log_info`, `log_error`, `log_success` | Structured logging |
| `require_command`, `require_env` | Validation |
| `ensure_buildx_builder` | Docker buildx setup |
| `image_exists_locally`, `get_image_digest` | Image helpers |

---

## 3. Knowledge Base (Spec Kit System)

Each skill has a **Spec Kit** - a quadrilateral documentation structure that serves as executable intent.

### Spec Kit Structure

```
spec/<skill-name>/
├── constitution.md    # Core principles, non-negotiables, governance
├── prd.md             # Product requirements, user stories, metrics
├── plan.md            # Technical architecture, implementation roadmap
└── tasks.md           # Task checklist with milestones
```

### Document Purposes

| Document | Purpose | Key Sections |
|----------|---------|--------------|
| `constitution.md` | Immutable rules | Principles, non-negotiables, scope |
| `prd.md` | What to build | Objectives, users, requirements, metrics |
| `plan.md` | How to build | Architecture, components, milestones |
| `tasks.md` | Execution tracking | Task checklist, acceptance criteria |

### Spec Kit Enforcement

CI validates spec structure (`.github/workflows/spec-kit-guard.yml`):

```yaml
- name: Validate spec kit structure
  run: |
    for spec in spec/*/; do
      for doc in constitution.md prd.md plan.md tasks.md; do
        if [[ ! -f "${spec}${doc}" ]]; then
          echo "Missing: ${spec}${doc}"
          exit 1
        fi
      done
    done
```

---

## 4. Multi-Agent Orchestration

The system supports deterministic multi-agent patterns using Claude Code commands.

### Agent Roles

| Role | Command | Purpose |
|------|---------|---------|
| **Planner** | `/project:plan` | Read specs, output change plan (no edits) |
| **Implementer** | `/project:implement` | Execute plan with minimal diffs |
| **Verifier** | `/project:verify` | Run checks, fix failures, rerun |
| **Orchestrator** | `/project:ship` | Coordinate full workflow |

### Workflow Contract

```
explore → plan → implement → verify → commit
```

### Command Files

Located in `.claude/commands/`:

**plan.md** (Planner)
```markdown
You are the PLANNER.
Input: $ARGUMENTS

Rules:
- Read relevant specs in spec/** first
- Output: Scope, File list, Risks, Verification commands, Tasks
- Do NOT implement. Do NOT edit files.
```

**implement.md** (Implementer)
```markdown
You are the IMPLEMENTER.
Input: $ARGUMENTS

Rules:
- Read the plan from spec/**/plan.md
- Make smallest code changes to satisfy plan
- Update docs and tests as required
- End with "Change Summary" and "Files Touched"
```

**verify.md** (Verifier)
```markdown
You are the VERIFIER.

Rules:
- Run: ./scripts/repo_health.sh && ./scripts/verify.sh
- If failures: identify cause, propose fix, apply, rerun
- End with: pass/fail status, remaining issues
```

**ship.md** (Orchestrator)
```markdown
Orchestrate full run:
1) /project:plan with request
2) /project:implement using plan
3) /project:verify until green
4) Prepare PR summary with intent, approach, evidence
```

---

## 5. Agent Configuration

### CLAUDE.md (Runtime Context)

Auto-loaded by Claude Code. Contains:
- Project operating rules
- Common commands
- Credential handling
- Verification standards

### .claude/settings.json (Tool Allowlist)

```json
{
  "allowedTools": [
    "Edit",
    "Bash(git status)",
    "Bash(git diff*)",
    "Bash(./scripts/verify.sh)",
    "Bash(./scripts/repo_health.sh)"
  ]
}
```

---

## 6. Verification System

### Standard Gates

| Script | Purpose |
|--------|---------|
| `scripts/repo_health.sh` | Check repo structure (CLAUDE.md, .claude/, etc.) |
| `scripts/verify.sh` | Run lint, typecheck, tests |
| `scripts/require_env.sh` | Validate required environment variables |

### Definition of Done

- Code compiles/runs
- Tests or checks pass
- Docs updated if behavior changed
- Commit message explains *why*, not just *what*

---

## 7. CI/CD Integration

### Path-Based Triggering

Skills only trigger CI when relevant files change:

```yaml
on:
  push:
    paths:
      - 'skills/docker-image-build/**'
```

### Agent-Aware CI

Skip heavy pipelines for docs-only changes:

```yaml
on:
  pull_request:
    paths-ignore:
      - 'spec/**'
      - '.claude/**'
      - 'CLAUDE.md'
      - 'docs/**'
```

---

## 8. Best Practices

### For Skill Development

1. **Source common.sh** - Don't reinvent utilities
2. **Use environment variables** - With sensible defaults
3. **Add Makefile targets** - For discoverability
4. **Write README.md** - Include examples and troubleshooting
5. **Create spec kit** - For complex skills

### For Agent Usage

1. **Read before write** - Always explore first
2. **Follow the contract** - explore → plan → implement → verify → commit
3. **Respect allowlists** - Don't bypass tool restrictions
4. **Verify always** - End every mutation with verification
5. **Evidence-based** - Show what was run and results

### For Spec Writing

1. **No placeholders** - TODO/TBD/LOREM are blocked by CI
2. **Substantive content** - Minimum 10 non-empty lines per file
3. **Actionable tasks** - Include acceptance criteria
4. **Link to code** - Reference actual file paths

---

## 9. Quick Reference

### Invocation Examples

```bash
# Direct script
./skills/docker-image-build/scripts/build.sh --load

# Via Makefile
make image-build IMAGE_TAG=v1.0.0

# Full workflow
make release-image IMAGE_TAG=v1.0.0

# Agent commands (in Claude Code)
/project:plan "add caching to API"
/project:implement
/project:verify
/project:ship
```

### Environment Variables

```bash
# Image builds
IMAGE_REPO=ghcr.io/org/repo
IMAGE_TAG=latest
PLATFORMS=linux/amd64,linux/arm64

# Tool enforcer (planned)
MCP_ENFORCER_LEVEL=advisory
MCP_ENFORCER_LOG=true
```

---

## 10. Troubleshooting

### Skill Not Running

1. Check script is executable: `chmod +x scripts/*.sh`
2. Verify common.sh is sourced
3. Check required environment variables

### CI Failing on Spec

1. Ensure all 4 files exist
2. Remove placeholders (TODO, TBD)
3. Add substantive content

### Agent Not Following Plan

1. Verify spec files are readable
2. Check CLAUDE.md is present
3. Review .claude/settings.json allowlist

---

## Further Reading

- [MCP Tool Enforcer Constitution](../spec/mcp-tool-enforcer-skill/constitution.md)
- [Docker Image Build README](../skills/docker-image-build/README.md)
- [CLAUDE.md](../CLAUDE.md)
