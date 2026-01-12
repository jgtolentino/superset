# AGENTS.md - Codex Agent Instructions

## Repository Context

This repository (`jgtolentino/superset`) is **infrastructure and configuration** for Apache Superset, NOT the Superset Python package itself.

### What This Repo Contains

```
jgtolentino/superset/
├── infra/
│   ├── do/                  # DigitalOcean App Platform specs
│   └── superset/            # Superset config & Dockerfile
├── scripts/                 # Automation & utility scripts
├── examples/                # Dashboard & dataset examples
├── docs/                    # Documentation
├── playwright/              # E2E test specs
└── .github/workflows/       # CI/CD pipelines
```

### What This Repo Does NOT Contain

- Superset Python source code
- `setup.py` or `pyproject.toml` at repo root
- The actual Superset application (installed from PyPI)

---

## Critical Instructions

### DO NOT

1. **DO NOT** run `pip install -e .` at repo root - this will fail
2. **DO NOT** try to modify Superset core code in this repo
3. **DO NOT** invent or hardcode credentials (see Credential Rules below)
4. **DO NOT** assume this is the apache/superset repo

### DO

1. **DO** install Superset from PyPI: `pip install apache-superset==4.0.1`
2. **DO** use environment variables for all credentials
3. **DO** run `./scripts/require_env.sh` before executing scripts
4. **DO** treat this as an infrastructure/deployment repo

---

## Credential Rules (STRICT)

### Required Environment Variables

```bash
BASE_URL                           # Superset instance URL
SUPERSET_ADMIN_USER                # Web UI login username
SUPERSET_ADMIN_PASS                # Web UI login password
EXAMPLES_DB_URI                    # PostgreSQL connection for examples
SUPERSET__SQLALCHEMY_DATABASE_URI  # Superset metadata DB
```

### Behavior

- If ANY required env var is missing: **STOP** and output `BLOCKED: missing env var <NAME>`
- If suspicious default values detected (admin, password, changeme): **STOP** and output `BLOCKED: suspicious default value in <VAR>`
- **NEVER** invent credentials or use placeholders as real values

---

## Common Tasks

### 1. Validate Environment

```bash
./scripts/require_env.sh
```

### 2. Run E2E Tests

```bash
npm install
npx playwright test
```

### 3. Deploy to DigitalOcean

```bash
doctl apps update <APP_ID> --spec infra/do/superset-app.yaml
```

### 4. Load Example Dashboards

```bash
./scripts/load_official_samples.sh
```

### 5. Database Migrations

```bash
./scripts/manage_migrations.sh
```

---

## Key Files

| File | Purpose |
|------|---------|
| `infra/do/superset-app.yaml` | DigitalOcean App Platform spec |
| `infra/superset/Dockerfile` | Superset container build |
| `infra/superset/superset_config.py` | Superset configuration |
| `scripts/require_env.sh` | Environment validation |
| `scripts/load_official_samples.sh` | Load example dashboards |
| `CLAUDE.md` | Claude Code agent instructions |

---

## GitHub Integration

To request PR reviews via Codex:

1. Ensure Codex GitHub app is installed on `jgtolentino/superset`
2. Comment `@codex review` on any PR
3. Codex will analyze and provide feedback

---

## Environment Setup

For Codex cloud environment, set these in **Codex Web > Settings > Environments**:

- **Org**: `jgtolentino`
- **Repo**: `jgtolentino/superset`
- **Image**: `universal`
- **Setup script**: Contents of `.codex/setup.sh`

Required environment variables (set in Codex, not in git):

```
SUPERSET_DATABASE_URI=postgresql+psycopg2://...
SUPERSET_REDIS_URL=redis://...
SUPERSET_GUEST_TOKEN_JWT_SECRET=...
DOCTL_ACCESS_TOKEN=...
```
