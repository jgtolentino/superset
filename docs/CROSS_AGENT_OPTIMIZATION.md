# Cross-Agent Optimization Framework
## Claude Code + Codex Unified Development Environment

**Generated**: 2026-01-12
**Target Repository**: jgtolentino/superset
**Agents**: Claude Code (Anthropic) + Codex (OpenAI)

---

# 1. Operational Summary

## Executive Summary

This document provides a unified framework for operating both Claude Code and OpenAI Codex as complementary AI coding agents. The framework enables:

- **Parallel task execution** across both agents for increased throughput
- **Consistent configuration** ensuring both agents follow the same project conventions
- **Unified security model** with appropriate sandboxing for both platforms
- **Seamless workflow handoffs** between cloud and local execution

## Engineering Summary

| Aspect | Claude Code | Codex |
|--------|-------------|-------|
| **Runtime** | Local CLI + VS Code | Local CLI + Cloud + iOS |
| **Language** | TypeScript/Node.js | Rust |
| **Config File** | CLAUDE.md + .claude/ | config.toml + AGENTS.md |
| **MCP Support** | Yes (.mcp.json) | Yes (mcp_servers in config.toml) |
| **Sandbox** | OS-level (bubblewrap/seatbelt) | Two-layer (sandbox + approval) |
| **Session Persistence** | Yes (--continue, --resume) | Yes (resume, cloud tasks) |
| **GitHub Integration** | Via MCP | Native (@codex review) |

## Key Insight

Both agents read instruction files from the project root:
- **Claude Code** reads `CLAUDE.md`
- **Codex** reads `AGENTS.md`

**Recommendation**: Maintain both files with synchronized content, or symlink one to the other.

---

# 2. Capability Matrix: Codex vs Claude Code

## Core Capabilities

| Capability | Claude Code | Codex | Notes |
|------------|-------------|-------|-------|
| Code Generation | Yes | Yes | Both support multi-file |
| Code Refactoring | Yes | Yes (51.3% success rate) | Codex benchmarked |
| Code Review | Yes | Yes (@codex review) | Codex has native GitHub |
| Debugging | Yes | Yes | Both support log analysis |
| Testing | Yes | Yes | Both generate tests |
| Documentation | Yes | Yes | Both can write docs |
| Web Search | Yes | Yes (--search) | Both support web access |
| File Operations | Yes | Yes | Both read/write files |
| Git Operations | Yes | Yes | Both support git |
| Shell Execution | Yes | Yes | Both run commands |

## Execution Modes

| Mode | Claude Code | Codex |
|------|-------------|-------|
| Interactive TUI | Yes (`claude`) | Yes (`codex`) |
| Non-interactive | Yes (`claude -p "..."`) | Yes (`codex exec "..."`) |
| Cloud/Async | No (local only) | Yes (`codex cloud`) |
| Resume Session | Yes (`--continue`) | Yes (`resume`) |
| Headless/CI | Yes (`--output-format json`) | Yes (`--quiet --json`) |
| Mobile | No | Yes (iOS app) |

## Configuration Surface

| Config Type | Claude Code | Codex |
|-------------|-------------|-------|
| Project Instructions | CLAUDE.md | AGENTS.md |
| Local/Private | CLAUDE.local.md | AGENTS.override.md |
| Settings File | .claude/settings.json | config.toml |
| MCP Config | .mcp.json | config.toml [mcp_servers] |
| Commands/Skills | .claude/commands/, .claude/skills/ | ~/.codex/skills/ |
| Hooks | .claude/hooks/ | Not supported |

## Security Model

| Feature | Claude Code | Codex |
|---------|-------------|-------|
| Filesystem Sandbox | Yes (OS-level) | Yes (workspace-write) |
| Network Isolation | Yes | Yes (disabled by default) |
| Approval Prompts | Yes (configurable) | Yes (4 policies) |
| Full Access Mode | --dangerously-skip-permissions | --yolo |
| Env Var Filtering | Via MCP | shell_environment_policy |

## Model Selection

| Agent | Available Models | Default |
|-------|------------------|---------|
| Claude Code | claude-sonnet-4-5, claude-opus-4-5 | claude-sonnet-4-5 |
| Codex | gpt-5.2-codex, gpt-5-codex, gpt-5.1-codex-mini | gpt-5.2-codex |

---

# 3. Workflow Templates

## 3.1 Code Generation Workflow

### Claude Code
```bash
# Interactive generation with context
claude
> Read src/models/ and generate a new UserPreferences model following existing patterns
> Write tests for UserPreferences in tests/models/

# Non-interactive generation
claude -p "Generate a REST API endpoint for user preferences in src/api/preferences.py following existing patterns in src/api/"
```

### Codex
```bash
# Interactive generation
codex
> Read src/models/ and generate a new UserPreferences model following existing patterns
> Write tests for UserPreferences in tests/models/

# Non-interactive generation
codex exec "Generate a REST API endpoint for user preferences in src/api/preferences.py following existing patterns in src/api/"

# Cloud generation (async)
codex cloud exec "Generate a REST API endpoint for user preferences"
codex apply  # Apply results locally
```

### Unified Template (AGENTS.md / CLAUDE.md)
```markdown
## Code Generation Guidelines

When generating new code:
1. Read existing patterns in the target directory first
2. Match naming conventions, imports, and structure
3. Include type hints and docstrings
4. Generate corresponding tests
5. Follow the error handling patterns in src/utils/errors.py
```

---

## 3.2 Refactoring Workflow

### Claude Code
```bash
claude
> Analyze src/legacy/ for code smells and technical debt
> Create a refactoring plan for the authentication module
> Execute the plan, running tests after each change
```

### Codex
```bash
codex -a on-request -s workspace-write
> Analyze src/legacy/ for code smells and technical debt
> Create a refactoring plan for the authentication module
> Execute the plan, running tests after each change
```

### Unified Template
```markdown
## Refactoring Protocol

Before refactoring:
1. Run full test suite: `npm test`
2. Create feature branch: `git checkout -b refactor/<module>`
3. Document current behavior

During refactoring:
1. Make atomic commits per change
2. Run tests after each change
3. Preserve public API unless explicitly changing

After refactoring:
1. Run full test suite
2. Run linter: `npm run lint`
3. Update documentation if APIs changed
```

---

## 3.3 Migration Workflow

### Claude Code
```bash
claude
> Analyze the database schema in migrations/
> Generate a migration to add user_preferences table
> Create corresponding model changes
> Update API endpoints to use new schema
```

### Codex
```bash
codex exec "Generate database migration for user_preferences table following patterns in migrations/"
```

### Unified Template
```markdown
## Database Migration Guidelines

Migration naming: YYYYMMDD_HHMMSS_description.py
Required steps:
1. Generate migration file
2. Add rollback (downgrade) logic
3. Update models/__init__.py exports
4. Add migration test
5. Update API documentation

Commands:
- Generate: `alembic revision --autogenerate -m "description"`
- Apply: `alembic upgrade head`
- Rollback: `alembic downgrade -1`
```

---

## 3.4 Debugging Workflow

### Claude Code
```bash
# Paste error and debug
claude -p "Debug this error: [paste traceback]
Context: This occurs when processing large CSV files in the import pipeline"
```

### Codex
```bash
codex exec "Debug this error: [paste traceback]
Context: This occurs when processing large CSV files in the import pipeline"
```

### Unified Template
```markdown
## Debugging Protocol

When debugging:
1. Reproduce the error with minimal test case
2. Check recent changes: `git log --oneline -10`
3. Verify environment: `./scripts/require_env.sh`
4. Check logs in: logs/, /var/log/superset/

Common issues:
- Database connection: Check SUPERSET__SQLALCHEMY_DATABASE_URI
- Authentication: Check SUPERSET_ADMIN_USER/PASS
- Memory: Check container limits
```

---

## 3.5 Repository Onboarding Workflow

### Claude Code
```bash
# Initialize project understanding
claude
> /init
> Summarize the architecture of this codebase
> What are the main entry points and how does data flow?
```

### Codex
```bash
codex
> Read AGENTS.md and summarize the project
> Explain the directory structure and key components
> What commands are available for development?
```

### Unified Template (for new team members)
```markdown
## Onboarding Checklist

1. Clone repository: `git clone <repo-url>`
2. Install dependencies: `./scripts/setup.sh`
3. Set environment variables (see .env.example)
4. Run tests: `npm test`
5. Start dev server: `npm run dev`

Key directories:
- src/api/ - REST endpoints
- src/models/ - Data models
- src/services/ - Business logic
- tests/ - Test suite
- docs/ - Documentation
```

---

## 3.6 Test Generation Workflow

### Claude Code
```bash
claude
> Analyze src/services/auth.py
> Generate comprehensive unit tests covering:
>   - Happy paths
>   - Edge cases
>   - Error conditions
>   - Boundary values
> Place tests in tests/services/test_auth.py
```

### Codex
```bash
codex exec "Generate comprehensive unit tests for src/services/auth.py including happy paths, edge cases, error conditions, and boundary values. Place in tests/services/test_auth.py"
```

### Unified Template
```markdown
## Test Generation Guidelines

Test file naming: test_<module>.py
Test function naming: test_<function>_<scenario>

Required coverage:
- Happy path (normal operation)
- Edge cases (empty inputs, large values)
- Error conditions (invalid inputs, failures)
- Boundary values (min/max limits)

Test commands:
- Run all: `pytest`
- Run specific: `pytest tests/services/test_auth.py`
- Coverage: `pytest --cov=src`
```

---

## 3.7 CI Review Workflow

### Claude Code (via MCP)
```bash
# Requires GitHub MCP server configured
claude
> Review the PR at https://github.com/org/repo/pull/123
> Focus on security issues and performance impacts
```

### Codex (Native)
```bash
# Comment on GitHub PR
@codex review

# Or via CLI
codex exec "Review PR #123 focusing on security and performance"
```

### Unified Template
```markdown
## Code Review Checklist

Security:
- [ ] No hardcoded credentials
- [ ] Input validation present
- [ ] SQL injection prevention
- [ ] XSS prevention

Performance:
- [ ] No N+1 queries
- [ ] Appropriate caching
- [ ] Async where beneficial

Quality:
- [ ] Tests included
- [ ] Documentation updated
- [ ] Follows style guide
```

---

# 4. Toolchain Integration Guide

## 4.1 GitHub Integration

### Claude Code Setup
```json
// .mcp.json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

### Codex Setup
```yaml
# .github/workflows/codex.yml
name: Codex Review
on:
  pull_request:
    types: [opened, synchronize]
  issue_comment:
    types: [created]

jobs:
  review:
    if: contains(github.event.comment.body, '@codex')
    runs-on: ubuntu-latest
    steps:
      - uses: openai/codex-action@v1
        with:
          openai-api-key: ${{ secrets.OPENAI_API_KEY }}
```

### Unified Commands
```bash
# Claude Code (via MCP)
claude -p "Review PR #123 and suggest improvements"

# Codex (native)
# Comment @codex review on PR
# Or:
codex exec "Fetch and review PR #123"
```

---

## 4.2 MCP Server Configuration

### Claude Code (.mcp.json)
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "DATABASE_URL": "${DATABASE_URL}"
      }
    }
  }
}
```

### Codex (config.toml)
```toml
[mcp_servers.filesystem]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-filesystem", "/workspace"]

[mcp_servers.github]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-github"]
env_vars = ["GITHUB_TOKEN"]

[mcp_servers.postgres]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-postgres"]
env_vars = ["DATABASE_URL"]
```

---

## 4.3 CI/CD Integration

### GitHub Actions (Unified)
```yaml
name: AI Agent Tasks
on:
  workflow_dispatch:
    inputs:
      task:
        description: 'Task for AI agent'
        required: true
      agent:
        description: 'Agent to use'
        required: true
        type: choice
        options:
          - claude
          - codex

jobs:
  claude:
    if: github.event.inputs.agent == 'claude'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install Claude Code
        run: npm install -g @anthropic-ai/claude-code
      - name: Execute Task
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          claude -p "${{ github.event.inputs.task }}" --output-format json

  codex:
    if: github.event.inputs.agent == 'codex'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install Codex
        run: npm install -g @openai/codex
      - name: Execute Task
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
        run: |
          codex exec "${{ github.event.inputs.task }}" --quiet --json
```

---

## 4.4 IDE Integration

### VS Code (Both Agents)
```json
// .vscode/settings.json
{
  "claude-code.enabled": true,
  "claude-code.autoConnect": true,
  "terminal.integrated.env.linux": {
    "ANTHROPIC_API_KEY": "${env:ANTHROPIC_API_KEY}",
    "OPENAI_API_KEY": "${env:OPENAI_API_KEY}"
  }
}
```

### VS Code Tasks
```json
// .vscode/tasks.json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Claude: Generate Tests",
      "type": "shell",
      "command": "claude -p 'Generate tests for ${file}'"
    },
    {
      "label": "Codex: Review File",
      "type": "shell",
      "command": "codex exec 'Review ${file} for issues'"
    }
  ]
}
```

---

## 4.5 Enterprise / On-Premises

### Air-Gapped Environment
```bash
# Claude Code: Use local models via Ollama MCP
# Codex: Use Azure OpenAI endpoint

# Configure Azure OpenAI for Codex
export OPENAI_API_BASE="https://your-resource.openai.azure.com"
export OPENAI_API_KEY="your-azure-key"
export OPENAI_API_TYPE="azure"
export OPENAI_API_VERSION="2024-02-15-preview"
```

### Enterprise Config (Codex)
```toml
# requirements.toml (organization-enforced)
allowed_approval_policies = ["untrusted", "on-request"]
blocked_approval_policies = ["never"]
allowed_sandbox_modes = ["workspace-write"]
blocked_sandbox_modes = ["danger-full-access"]
```

---

# 5. Local Config Bundles

## 5.1 config.toml (Codex)

```toml
# ~/.codex/config.toml
# Codex CLI Configuration for jgtolentino/superset

# =============================================================================
# Model Configuration
# =============================================================================
model = "gpt-5.2-codex"
review_model = "gpt-5.2-codex"

# =============================================================================
# Security Configuration
# =============================================================================
approval_policy = "on-request"
sandbox_mode = "workspace-write"

[sandbox_workspace_write]
network_access = false  # Enable only when needed for package installs

# =============================================================================
# Shell Environment Policy
# =============================================================================
[shell_environment_policy]
inherit = "core"
exclude = [
  "AWS_*",
  "AZURE_*",
  "*_SECRET*",
  "*_PASSWORD*",
  "*_TOKEN*",
  "*_KEY*"
]
include = [
  "PATH",
  "HOME",
  "USER",
  "SHELL",
  "TERM",
  "LANG",
  "LC_*",
  "NODE_ENV",
  "PYTHON*",
  "VIRTUAL_ENV"
]

# =============================================================================
# Project Detection
# =============================================================================
project_root_markers = [".git", "package.json", "pyproject.toml", "Cargo.toml"]
project_doc_fallback_filenames = ["AGENTS.md", "CLAUDE.md", "README.md"]

# =============================================================================
# MCP Servers
# =============================================================================
[mcp_servers.filesystem]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-filesystem", "."]

[mcp_servers.github]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-github"]
env_vars = ["GITHUB_TOKEN"]

# =============================================================================
# Profiles
# =============================================================================
[profiles.safe]
approval_policy = "untrusted"
sandbox_mode = "workspace-write"

[profiles.auto]
approval_policy = "on-request"
sandbox_mode = "workspace-write"

[profiles.full]
approval_policy = "never"
sandbox_mode = "workspace-write"
```

---

## 5.2 claude.config (Claude Code Settings)

```json
{
  "$schema": "https://code.claude.com/schemas/settings.json",
  "permissions": {
    "allow": [
      "Bash(npm *)",
      "Bash(npx *)",
      "Bash(pip *)",
      "Bash(python *)",
      "Bash(pytest *)",
      "Bash(git *)",
      "Bash(make *)",
      "Bash(docker compose *)",
      "Read(*)",
      "Write(src/*)",
      "Write(tests/*)",
      "Write(docs/*)"
    ],
    "deny": [
      "Bash(rm -rf /)",
      "Bash(sudo *)",
      "Bash(curl * | sh)",
      "Bash(wget * | sh)",
      "Write(.env*)",
      "Write(*secret*)",
      "Write(*credential*)"
    ]
  },
  "sandbox": {
    "enabled": true,
    "networkAccess": false
  },
  "model": "claude-sonnet-4-5",
  "outputFormat": "markdown"
}
```

---

## 5.3 AGENTS.md (Unified)

```markdown
# AGENTS.md - Project Instructions for AI Agents

## Repository Context

This repository (`jgtolentino/superset`) is **infrastructure and configuration** for Apache Superset.

**This is NOT the Superset Python package.**

- Install Superset from PyPI: `pip install apache-superset==4.0.1`
- Do NOT run `pip install -e .` at repo root

## Directory Structure

```
jgtolentino/superset/
├── infra/
│   ├── do/              # DigitalOcean deployment specs
│   └── superset/        # Superset config & Dockerfile
├── scripts/             # Automation scripts
├── examples/            # Dashboard examples
├── docs/                # Documentation
├── playwright/          # E2E test specs
└── .github/workflows/   # CI/CD pipelines
```

## Build & Test Commands

```bash
# Environment setup
./scripts/require_env.sh        # Validate environment

# Testing
npm install                     # Install Node dependencies
npx playwright test             # Run E2E tests

# Python environment (for scripts)
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Required Environment Variables

```bash
BASE_URL                           # Superset instance URL
SUPERSET_ADMIN_USER                # Web UI username
SUPERSET_ADMIN_PASS                # Web UI password
EXAMPLES_DB_URI                    # PostgreSQL for examples
SUPERSET__SQLALCHEMY_DATABASE_URI  # Metadata DB
```

## Credential Rules (STRICT)

- **NEVER** invent or hardcode credentials
- **ALWAYS** use environment variables
- **STOP** if any required env var is missing
- Output: `BLOCKED: missing env var <NAME>`

## Git Workflow

```bash
# Branch naming
feature/<name>
fix/<name>
refactor/<name>

# Commit format
<type>: <description>

# Types: feat, fix, refactor, test, docs, chore
```

## Security Guidelines

- No credentials in code, docs, or commits
- Use `.env` files (gitignored) for local dev
- Use platform secrets for production
- Run preflight checks before scripts

## Code Review Focus

- Security: No hardcoded secrets, proper input validation
- Performance: No N+1 queries, appropriate caching
- Quality: Tests included, documentation updated

## Deployment

```bash
# DigitalOcean
doctl apps update <APP_ID> --spec infra/do/superset-app.yaml

# Docker
docker-compose --env-file .env up
```
```

---

# 6. Cloud Config Bundles

## 6.1 Codex Cloud Environment

### Setup in Codex Web UI

**Settings > Environments**

| Field | Value |
|-------|-------|
| Org | jgtolentino |
| Repo | jgtolentino/superset |
| Image | universal |
| Setup script | See below |

### Setup Script
```bash
#!/usr/bin/env bash
set -euo pipefail

cd /workspace/superset

# Python environment
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel setuptools --quiet

# Install Superset from PyPI
pip install "apache-superset==4.0.1" --quiet

# Repo dependencies
if [ -f "requirements.txt" ]; then
  pip install -r requirements.txt --quiet
fi

# Node.js for Playwright
if [ -f "playwright.config.ts" ]; then
  npm install --quiet
  npx playwright install chromium --quiet
fi

echo "Environment ready"
```

### Environment Variables (in Codex, not git)
```
SUPERSET_DATABASE_URI=postgresql+psycopg2://user:pass@host/db
SUPERSET_REDIS_URL=redis://host:6379
SUPERSET_GUEST_TOKEN_JWT_SECRET=<secret>
GITHUB_TOKEN=<token>
DOCTL_ACCESS_TOKEN=<token>
```

---

## 6.2 GitHub Codespaces

### devcontainer.json
```json
{
  "name": "Superset Infra Dev",
  "image": "mcr.microsoft.com/devcontainers/universal:2",
  "features": {
    "ghcr.io/devcontainers/features/python:1": {
      "version": "3.11"
    },
    "ghcr.io/devcontainers/features/node:1": {
      "version": "20"
    }
  },
  "postCreateCommand": "./.codex/setup.sh",
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "dbaeumer.vscode-eslint",
        "esbenp.prettier-vscode"
      ]
    }
  },
  "secrets": {
    "ANTHROPIC_API_KEY": {
      "description": "Claude Code API key"
    },
    "OPENAI_API_KEY": {
      "description": "Codex API key"
    }
  }
}
```

---

## 6.3 Secrets Injection Patterns

### GitHub Actions
```yaml
env:
  SUPERSET_ADMIN_USER: ${{ secrets.SUPERSET_ADMIN_USER }}
  SUPERSET_ADMIN_PASS: ${{ secrets.SUPERSET_ADMIN_PASS }}
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

### Docker Compose
```yaml
# docker-compose.yml
services:
  superset:
    env_file:
      - .env  # gitignored
```

### Kubernetes
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: superset-secrets
type: Opaque
stringData:
  SUPERSET_ADMIN_USER: "${SUPERSET_ADMIN_USER}"
  SUPERSET_ADMIN_PASS: "${SUPERSET_ADMIN_PASS}"
```

---

## 6.4 CI-Based Dependency Sync

```yaml
# .github/workflows/sync-deps.yml
name: Sync Dependencies
on:
  push:
    paths:
      - 'requirements.txt'
      - 'package.json'
  schedule:
    - cron: '0 0 * * 0'  # Weekly

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          npm ci

      - name: Update lockfiles
        run: |
          pip freeze > requirements.lock

      - name: Commit if changed
        run: |
          git config user.name github-actions
          git config user.email github-actions@github.com
          git add -A
          git diff --staged --quiet || git commit -m "chore: sync dependency lockfiles"
          git push
```

---

# 7. Security & Sandbox Profile

## 7.1 Unified Security Model

### Allowed Operations

| Operation | Claude Code | Codex | Risk Level |
|-----------|-------------|-------|------------|
| Read any file | Yes | Yes | Low |
| Write to src/ | Yes | Yes | Medium |
| Write to tests/ | Yes | Yes | Low |
| Write to docs/ | Yes | Yes | Low |
| Run npm/pip | Yes | Yes | Medium |
| Run pytest | Yes | Yes | Low |
| Run git commands | Yes | Yes | Low |
| Network access | No (default) | No (default) | High |
| Write to .env | No | No | Critical |
| Sudo commands | No | No | Critical |

### Disallowed Operations

| Operation | Reason |
|-----------|--------|
| `rm -rf /` | Destructive |
| `sudo *` | Privilege escalation |
| `curl * \| sh` | Remote code execution |
| Write to .env* | Credential exposure |
| Write to *secret* | Credential exposure |
| Network to unknown hosts | Data exfiltration |

---

## 7.2 Reasoning Modes

### Claude Code
- **Default**: Interactive with approval prompts
- **Autonomous**: With sandbox enabled, reduced prompts
- **Headless**: Non-interactive for CI/CD

### Codex
- **untrusted**: Prompt for everything
- **on-request**: Prompt for sensitive operations
- **on-failure**: Prompt only on errors
- **never**: No prompts (requires workspace-write)

### Recommended Settings

| Environment | Claude Code | Codex |
|-------------|-------------|-------|
| Development | sandbox + interactive | on-request + workspace-write |
| CI/CD | headless + restricted | on-request + workspace-write |
| Production | not recommended | not recommended |

---

## 7.3 Filesystem Rules

### Writable Paths
```
src/
tests/
docs/
examples/
scripts/
playwright/
.github/workflows/
```

### Read-Only Paths
```
infra/
node_modules/
.venv/
```

### Forbidden Paths
```
.env*
*credentials*
*secrets*
~/.ssh/
~/.aws/
~/.config/
```

---

## 7.4 Network Rules

### Allowed Domains (when network enabled)
```
registry.npmjs.org
pypi.org
files.pythonhosted.org
github.com
api.github.com
```

### Blocked Domains
```
* (all by default)
```

### Enabling Network Access

**Claude Code**:
```json
{
  "sandbox": {
    "networkAccess": true,
    "allowedDomains": ["registry.npmjs.org", "pypi.org"]
  }
}
```

**Codex**:
```toml
[sandbox_workspace_write]
network_access = true
```

---

# 8. Optimization Recommendations

## 8.1 Latency Improvements

| Recommendation | Impact | Implementation |
|----------------|--------|----------------|
| Use faster models for simple tasks | High | Claude: sonnet-4-5, Codex: mini |
| Enable prompt caching | High | Both support cached context |
| Pre-load project context | Medium | Keep AGENTS.md/CLAUDE.md concise |
| Use non-interactive mode for CI | High | `claude -p` / `codex exec` |
| Parallel task execution | High | Multiple agent instances |

### Model Selection Strategy
```bash
# Simple tasks (lint, format, small fixes)
claude --model claude-sonnet-4-5 -p "Fix linting errors"
codex -m gpt-5.1-codex-mini exec "Fix linting errors"

# Complex tasks (architecture, refactoring)
claude --model claude-opus-4-5 -p "Redesign authentication module"
codex -m gpt-5.2-codex exec "Redesign authentication module"
```

---

## 8.2 Project Indexing Improvements

### AGENTS.md / CLAUDE.md Best Practices
```markdown
# Keep these sections minimal:
- Build commands (exact, no prose)
- Test commands (exact, no prose)
- Directory map (structure only)
- Critical constraints (security, style)

# Move to separate docs:
- Architecture details → docs/ARCHITECTURE.md
- API documentation → docs/API.md
- Detailed conventions → docs/CONVENTIONS.md
```

### Import External Docs (Claude Code)
```markdown
# CLAUDE.md
See @docs/ARCHITECTURE.md for system design.
See @docs/API.md for endpoint documentation.
```

---

## 8.3 Prompt Engineering Improvements

### Structured Prompts
```markdown
## Task: [Clear objective]

### Context
- Current state: [description]
- Relevant files: [list]
- Constraints: [requirements]

### Requirements
1. [Specific requirement]
2. [Specific requirement]

### Expected Output
- [Deliverable]
- [Deliverable]

### Validation
- Run: [test command]
- Check: [verification step]
```

### Anti-Patterns to Avoid
```markdown
# Bad: Vague
"Fix the authentication"

# Good: Specific
"Fix the JWT token refresh logic in src/auth/jwt.py that causes 401 errors after 1 hour. The refresh should happen automatically when token expires within 5 minutes."
```

---

## 8.4 Toolchain Alignment

### Unified Scripts
```bash
#!/usr/bin/env bash
# scripts/ai-task.sh - Works with both Claude Code and Codex

AGENT="${1:-claude}"
TASK="$2"

case "$AGENT" in
  claude)
    claude -p "$TASK" --output-format json
    ;;
  codex)
    codex exec "$TASK" --quiet --json
    ;;
  both)
    echo "=== Claude Code ==="
    claude -p "$TASK"
    echo "=== Codex ==="
    codex exec "$TASK"
    ;;
esac
```

---

## 8.5 Secrets Handling Patterns

### Environment Loading
```bash
# scripts/load-env.sh
#!/usr/bin/env bash
set -euo pipefail

# Load from .env if exists
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

# Validate required vars
REQUIRED_VARS=(
  "SUPERSET_ADMIN_USER"
  "SUPERSET_ADMIN_PASS"
  "BASE_URL"
)

for var in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!var:-}" ]; then
    echo "BLOCKED: missing env var $var"
    exit 1
  fi
done

echo "Environment validated"
```

### Secret Rotation
```yaml
# .github/workflows/rotate-secrets.yml
name: Secret Rotation Reminder
on:
  schedule:
    - cron: '0 0 1 * *'  # Monthly

jobs:
  remind:
    runs-on: ubuntu-latest
    steps:
      - name: Create Issue
        uses: actions/github-script@v7
        with:
          script: |
            github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: 'Monthly Secret Rotation Reminder',
              body: 'Review and rotate secrets if needed:\n- SUPERSET_ADMIN_PASS\n- API tokens\n- Database credentials'
            })
```

---

## 8.6 Memory & Context Preservation

### Session Management
```bash
# Claude Code: Resume last session
claude --continue

# Claude Code: Resume specific session
claude --resume abc123

# Codex: Resume session
codex resume --last

# Codex: Cloud task continuation
codex cloud
# Select task to continue
```

### Context Optimization
```markdown
# Keep in AGENTS.md/CLAUDE.md (always loaded):
- Critical commands
- Security constraints
- Directory structure

# Keep in separate files (loaded on demand):
- Detailed architecture
- API documentation
- Historical decisions
```

### Memory Extension (Claude Code)
```json
// .mcp.json - Add memory server
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "mcp-memory-keeper"],
      "env": {
        "MEMORY_PATH": ".claude/memory.json"
      }
    }
  }
}
```

---

## 8.7 Ranked Optimization Summary

| Priority | Optimization | Effort | Impact |
|----------|--------------|--------|--------|
| 1 | Keep AGENTS.md/CLAUDE.md minimal | Low | High |
| 2 | Use appropriate model for task complexity | Low | High |
| 3 | Enable sandbox for autonomous work | Low | High |
| 4 | Use non-interactive mode for CI/CD | Low | High |
| 5 | Configure MCP servers for integrations | Medium | High |
| 6 | Set up parallel task execution | Medium | High |
| 7 | Implement session resumption | Low | Medium |
| 8 | Add memory persistence (Claude) | Medium | Medium |
| 9 | Configure prompt caching | Low | Medium |
| 10 | Set up unified scripts | Medium | Medium |

---

# Appendix: Quick Reference

## Claude Code Commands
```bash
claude                          # Interactive
claude -p "task"                # Non-interactive
claude --continue               # Resume last
claude --resume ID              # Resume specific
claude /init                    # Initialize CLAUDE.md
claude /sandbox                 # Enable sandbox
claude /permissions             # Configure permissions
```

## Codex Commands
```bash
codex                           # Interactive
codex exec "task"               # Non-interactive
codex resume                    # Resume picker
codex cloud exec "task"         # Cloud task
codex apply                     # Apply cloud results
codex status                    # Show config
/approvals auto                 # Switch approval mode
/elevate-sandbox                # Request elevated access
```

## File Locations
```
# Claude Code
CLAUDE.md                       # Project instructions
CLAUDE.local.md                 # Private preferences
.claude/settings.json           # Permissions
.claude/commands/               # Slash commands
.claude/skills/                 # Skills
.mcp.json                       # MCP servers

# Codex
AGENTS.md                       # Project instructions
AGENTS.override.md              # Temporary overrides
~/.codex/config.toml            # Global config
.codex/config.toml              # Project config
~/.codex/skills/                # Skills
```
