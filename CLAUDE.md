# CLAUDE.md — Superset Repo Execution Rules

## Credential Handling (STRICT)

- **Never invent credentials** (no fake usernames/passwords)
- **Never hardcode secrets** in prompts, code, docs, or commits
- **All credentials must come from** environment variables or secret stores

### Required Environment Variables

```bash
# Superset instance
BASE_URL                           # e.g., https://superset.insightpulseai.net

# Superset admin credentials
SUPERSET_ADMIN_USER                # Web UI login username
SUPERSET_ADMIN_PASS                # Web UI login password

# Data source connection
EXAMPLES_DB_URI                    # PostgreSQL connection for examples schema

# Metadata database connection
SUPERSET__SQLALCHEMY_DATABASE_URI  # Superset metadata DB (MUST be PostgreSQL, NOT SQLite)
```

### Behavior Rules

**If any required env var is missing or empty:**
- ❌ **STOP immediately**
- ❌ **Output**: `BLOCKED: missing env var <NAME>`
- ❌ **Do NOT proceed** with assumed or placeholder credentials

**If suspicious default values detected:**
- ❌ **STOP immediately**
- ❌ **Output**: `BLOCKED: suspicious default value in <VAR>`
- ❌ **Do NOT proceed** with generic defaults like "admin", "password", "changeme"

### Credential Storage

**✅ Allowed:**
- Environment variables from `~/.zshrc` (local dev)
- `.env` files (gitignored, loaded with direnv/docker-compose)
- Platform secrets (DigitalOcean, Kubernetes, GitHub Actions)
- Secret stores (Vault, AWS Secrets Manager, etc.)

**❌ Forbidden:**
- Hardcoded credentials in code, docs, or prompts
- Committed `.env` files
- Credentials in git history
- Credentials in documentation examples (use placeholders like `[SUPERSET_LOGIN_USER]`)

## Execution Model

### Before Any Operation
All scripts MUST run preflight check:
```bash
./scripts/require_env.sh
```

This validates:
1. All required env vars are set
2. No suspicious default values detected
3. Credentials are properly loaded

### Verification Protocol

**No false success claims:**
- All "success" claims MUST show real tool output
- Use "Expected Output (Sample)" if showing examples
- Link to actual CI artifacts or test runs for verification

**Evidence requirements:**
- API responses with real data (redact tokens)
- Screenshots from actual deployments
- Log outputs from real command execution
- Test results from CI/CD pipelines

## Repository Standards

### Security
- ✅ `.gitignore` protects sensitive files (`.env`, `*.log`, `artifacts/`)
- ✅ No credentials in committed files
- ✅ Placeholder credentials in documentation (`[SUPERSET_LOGIN_USER]`)
- ✅ Preflight checks prevent execution with missing/suspicious credentials

### Quality Gates
- ✅ All scripts validate environment before execution
- ✅ Fail fast on missing credentials
- ✅ Clear error messages for debugging
- ✅ Evidence-based validation (no assumed success)

## Platform-Specific Secrets

### Local Development
```bash
# ~/.zshrc (for persistent credentials)
export SUPERSET_ADMIN_USER="actual_username"
export SUPERSET_ADMIN_PASS="actual_password"
# ... etc
```

### DigitalOcean App Platform
Set via `doctl apps update` with encrypted environment variables:
```bash
doctl apps update <APP_ID> --spec infra/do/superset-app.yaml
# spec includes env_vars with encrypted values
```

### GitHub Actions
Set via repository secrets:
```yaml
env:
  SUPERSET_ADMIN_USER: ${{ secrets.SUPERSET_ADMIN_USER }}
  SUPERSET_ADMIN_PASS: ${{ secrets.SUPERSET_ADMIN_PASS }}
```

### Docker Compose
Use `.env` file (gitignored):
```bash
docker-compose --env-file .env up
```

## Troubleshooting

### "BLOCKED: missing env var"
**Cause**: Required environment variable not set

**Fix**:
```bash
# Check which vars are set
env | grep SUPERSET

# Add to ~/.zshrc
export SUPERSET_ADMIN_USER="your_username"
source ~/.zshrc

# Or use .env file
echo "SUPERSET_ADMIN_USER=your_username" >> .env
```

### "BLOCKED: suspicious default value"
**Cause**: Generic placeholder detected (e.g., "admin", "password")

**Fix**: Set actual production credentials
```bash
export SUPERSET_ADMIN_USER="real_username_not_admin"
export SUPERSET_ADMIN_PASS="real_password_not_password"
```

### Authentication failures in scripts
**Cause**: Credentials not loaded or incorrect

**Debug**:
```bash
# Verify credentials are loaded
./scripts/require_env.sh

# Check credential values (redacted)
echo "User: $SUPERSET_ADMIN_USER"
echo "Pass length: ${#SUPERSET_ADMIN_PASS}"

# Test authentication manually
curl -X POST "$BASE_URL/api/v1/security/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$SUPERSET_ADMIN_USER\",\"password\":\"$SUPERSET_ADMIN_PASS\",\"provider\":\"db\"}"
```
