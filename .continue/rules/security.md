# Security Rules

> Security requirements and credential handling for the Notion Finance PPM Control Room

## Core Security Principles

### 1. Zero Trust

- Authenticate and authorize every request
- Never assume internal networks are safe
- Validate all inputs at system boundaries
- Log all access for audit

### 2. Defense in Depth

- Multiple layers of security controls
- No single point of failure
- Assume breach and limit blast radius
- Encrypt data at rest and in transit

### 3. Least Privilege

- Grant minimum required permissions
- Use service principals with scoped access
- Rotate credentials regularly
- Review access periodically

---

## Credential Management

### Required Environment Variables

```bash
# Notion Integration
NOTION_API_KEY              # Internal integration token

# Databricks
DATABRICKS_HOST             # Workspace URL
DATABRICKS_TOKEN            # PAT or OAuth token
DATABRICKS_WAREHOUSE_ID     # SQL warehouse ID

# Azure
AZURE_SUBSCRIPTION_ID       # Subscription GUID
AZURE_TENANT_ID             # Tenant GUID
AZURE_CLIENT_ID             # Service principal app ID
AZURE_CLIENT_SECRET         # Service principal secret

# Application
API_SECRET_KEY              # For signing tokens
ALLOWED_ORIGINS             # CORS origins (comma-separated)
```

### Credential Sources (Allowed)

| Environment | Source |
|-------------|--------|
| Local Development | `.env` file (gitignored) |
| CI/CD | GitHub Secrets |
| Production | Azure Key Vault |
| Databricks | Workspace secrets scope |

### Credential Sources (Prohibited)

- Hardcoded in source code
- Committed to git (any branch)
- Stored in documentation
- Passed via URL parameters
- Logged to stdout/files

### Preflight Check

All scripts must validate credentials before execution:

```bash
#!/bin/bash
# scripts/require_env.sh

set -e

REQUIRED_VARS=(
    "NOTION_API_KEY"
    "DATABRICKS_HOST"
    "DATABRICKS_TOKEN"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [[ -z "${!var}" ]]; then
        echo "BLOCKED: missing env var $var"
        exit 1
    fi

    # Check for suspicious defaults
    if [[ "${!var}" == "changeme" ]] || \
       [[ "${!var}" == "password" ]] || \
       [[ "${!var}" == "secret" ]]; then
        echo "BLOCKED: suspicious default value in $var"
        exit 1
    fi
done

echo "Environment validated successfully"
```

---

## API Security

### Authentication

```typescript
// middleware.ts
import { NextRequest, NextResponse } from 'next/server';
import { verifyToken } from '@/lib/auth';

export async function middleware(request: NextRequest) {
  // Skip auth for health check
  if (request.nextUrl.pathname === '/api/health') {
    return NextResponse.next();
  }

  const authHeader = request.headers.get('authorization');
  if (!authHeader?.startsWith('Bearer ')) {
    return NextResponse.json(
      { error: { code: 'UNAUTHORIZED', message: 'Missing token' } },
      { status: 401 }
    );
  }

  const token = authHeader.slice(7);
  const payload = await verifyToken(token);

  if (!payload) {
    return NextResponse.json(
      { error: { code: 'UNAUTHORIZED', message: 'Invalid token' } },
      { status: 401 }
    );
  }

  // Add user to headers for downstream handlers
  const response = NextResponse.next();
  response.headers.set('x-user-id', payload.sub);
  return response;
}

export const config = {
  matcher: '/api/:path*',
};
```

### Authorization

```typescript
// lib/auth.ts
type Permission = 'read:kpis' | 'read:jobs' | 'write:actions' | 'admin';

interface User {
  id: string;
  email: string;
  roles: string[];
  permissions: Permission[];
}

const ROLE_PERMISSIONS: Record<string, Permission[]> = {
  viewer: ['read:kpis', 'read:jobs'],
  editor: ['read:kpis', 'read:jobs', 'write:actions'],
  admin: ['read:kpis', 'read:jobs', 'write:actions', 'admin'],
};

export function authorize(user: User, required: Permission): boolean {
  return user.permissions.includes(required) ||
         user.permissions.includes('admin');
}
```

### Rate Limiting

```typescript
// lib/rate-limit.ts
import { Ratelimit } from '@upstash/ratelimit';
import { Redis } from '@upstash/redis';

export const rateLimiter = new Ratelimit({
  redis: Redis.fromEnv(),
  limiter: Ratelimit.slidingWindow(100, '1 m'),
  analytics: true,
});

// In API route
export async function GET(request: NextRequest) {
  const identifier = request.headers.get('x-user-id') || 'anonymous';
  const { success, limit, remaining } = await rateLimiter.limit(identifier);

  if (!success) {
    return NextResponse.json(
      { error: { code: 'RATE_LIMITED', message: 'Too many requests' } },
      {
        status: 429,
        headers: {
          'X-RateLimit-Limit': limit.toString(),
          'X-RateLimit-Remaining': remaining.toString(),
        },
      }
    );
  }

  // Continue with request...
}
```

### Input Validation

```typescript
// Always validate with Zod
import { z } from 'zod';

const CreateActionSchema = z.object({
  project_id: z.string().uuid().optional(),
  title: z.string().min(1).max(500),
  description: z.string().max(5000).optional(),
  assignee: z.string().email().optional(),
  due_date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/).optional(),
  source: z.enum(['advisor', 'dq', 'manual']),
  source_id: z.string().optional(),
  priority: z.enum(['high', 'medium', 'low']).optional(),
});

// In handler
const result = CreateActionSchema.safeParse(await request.json());
if (!result.success) {
  return NextResponse.json(
    { error: { code: 'VALIDATION_ERROR', details: result.error.issues } },
    { status: 400 }
  );
}
```

---

## Data Security

### Encryption

| Data State | Method |
|------------|--------|
| At Rest (Databricks) | Delta encryption, Azure managed keys |
| At Rest (API) | Not applicable (stateless) |
| In Transit | TLS 1.3 |
| Secrets | Azure Key Vault encryption |

### Data Classification

| Classification | Examples | Handling |
|----------------|----------|----------|
| Public | Job names, table schemas | Standard protection |
| Internal | KPIs, budget data | Auth required, audit logged |
| Confidential | API keys, credentials | Encrypted, vault storage |
| Restricted | PII (if any) | Special handling, minimize |

### Data Minimization

- Only sync required Notion fields
- Don't store PII unless necessary
- Aggregate data in gold layer
- Set retention policies

---

## Infrastructure Security

### Network Security

```bicep
// Databricks workspace with VNet injection
resource databricksWorkspace 'Microsoft.Databricks/workspaces@2023-02-01' = {
  properties: {
    managedResourceGroupId: managedResourceGroup.id
    parameters: {
      customVirtualNetworkId: {
        value: vnet.id
      }
      customPublicSubnetName: {
        value: publicSubnet.name
      }
      customPrivateSubnetName: {
        value: privateSubnet.name
      }
      enableNoPublicIp: {
        value: true
      }
    }
  }
}
```

### Secret Management

```python
# Databricks secret access
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# Get secret from scope
notion_key = w.secrets.get_secret(
    scope="ppm-secrets",
    key="notion-api-key"
).value

# Never log secrets
logger.info("Notion client initialized")  # Good
# logger.info(f"Using key: {notion_key}")  # BAD - never do this
```

### Container Security

```dockerfile
# Use minimal base image
FROM python:3.11-slim

# Run as non-root
RUN useradd --create-home appuser
USER appuser

# Don't copy secrets
COPY --chown=appuser:appuser . /app
# Use runtime env vars for secrets

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:8000/health || exit 1
```

---

## Audit & Compliance

### Audit Logging

```typescript
// lib/audit.ts
interface AuditEvent {
  timestamp: string;
  user_id: string;
  action: string;
  resource: string;
  resource_id?: string;
  details?: Record<string, unknown>;
  ip_address?: string;
  user_agent?: string;
}

export async function logAuditEvent(event: AuditEvent): Promise<void> {
  // Write to structured log
  console.log(JSON.stringify({
    type: 'audit',
    ...event,
  }));

  // Also write to audit table if configured
  if (process.env.AUDIT_TABLE_ENABLED) {
    await writeToAuditTable(event);
  }
}
```

### Sensitive Data in Logs

```python
# Never log sensitive data
import re

def sanitize_log(message: str) -> str:
    """Remove sensitive patterns from log messages."""
    patterns = [
        (r'Bearer [a-zA-Z0-9\-_\.]+', 'Bearer [REDACTED]'),
        (r'api[_-]?key["\s:=]+[a-zA-Z0-9\-_]+', 'api_key=[REDACTED]'),
        (r'password["\s:=]+[^\s,}]+', 'password=[REDACTED]'),
        (r'secret["\s:=]+[^\s,}]+', 'secret=[REDACTED]'),
    ]

    for pattern, replacement in patterns:
        message = re.sub(pattern, replacement, message, flags=re.IGNORECASE)

    return message
```

### Access Reviews

Monthly review checklist:
- [ ] Review service principal permissions
- [ ] Review API key usage
- [ ] Check for unused credentials
- [ ] Verify audit log retention
- [ ] Review RBAC assignments

---

## Incident Response

### Security Incident Process

1. **Detect**: Alerts, logs, user reports
2. **Contain**: Revoke credentials, disable access
3. **Investigate**: Audit logs, timeline
4. **Remediate**: Rotate secrets, patch vulnerabilities
5. **Review**: Post-mortem, update procedures

### Credential Rotation

```bash
# Rotate Notion API key
# 1. Create new integration in Notion
# 2. Update Key Vault
az keyvault secret set \
  --vault-name "$VAULT_NAME" \
  --name "notion-api-key" \
  --value "$NEW_KEY"

# 3. Restart services to pick up new key
# 4. Revoke old key in Notion

# 5. Verify
./scripts/health_check.sh
```

---

## OWASP Top 10 Considerations

| Risk | Mitigation |
|------|------------|
| A01: Broken Access Control | RBAC, permission checks, audit |
| A02: Cryptographic Failures | TLS, Key Vault, no hardcoded secrets |
| A03: Injection | Parameterized queries, input validation |
| A04: Insecure Design | Security reviews, threat modeling |
| A05: Security Misconfiguration | IaC, secure defaults, no debug in prod |
| A06: Vulnerable Components | Dependency scanning, updates |
| A07: Auth Failures | JWT, rate limiting, account lockout |
| A08: Software/Data Integrity | Signed packages, SRI, CI checks |
| A09: Logging Failures | Structured logging, log sanitization |
| A10: SSRF | URL allowlisting, no user-controlled URLs |
