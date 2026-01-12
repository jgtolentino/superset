# InsightPulse AI Platform Architecture

## Services Overview

| Service | URL | Purpose |
|---------|-----|---------|
| **MCP Server** | https://mcp.insightpulseai.net | Model Context Protocol gateway for AI agent integrations |
| **n8n** | https://n8n.insightpulseai.net | Workflow automation and orchestration |
| **Superset** | https://superset.insightpulseai.net | BI dashboards and data visualization |

---

# 1. MCP Server Design (mcp.insightpulseai.net)

## 1.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                                      │
├─────────────────────────────────────────────────────────────────────────┤
│  Claude Code  │  Codex CLI  │  VS Code  │  Custom Agents  │  n8n        │
└───────┬───────┴──────┬──────┴─────┬─────┴───────┬─────────┴──────┬──────┘
        │              │            │             │                │
        ▼              ▼            ▼             ▼                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     API GATEWAY LAYER                                    │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  ┌───────────────┐  │
│  │ Load        │  │ Rate         │  │ OAuth 2.0  │  │ Circuit       │  │
│  │ Balancer    │  │ Limiting     │  │ Auth       │  │ Breaker       │  │
│  └─────────────┘  └──────────────┘  └────────────┘  └───────────────┘  │
│                     Traefik / Nginx / Kong                              │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     MCP SERVER LAYER                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    MCP Router / Gateway                          │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │   │
│  │  │ Tools    │  │ Resources│  │ Prompts  │  │ Tasks (Nov 2025) │ │   │
│  │  │ Registry │  │ Registry │  │ Registry │  │ Manager          │ │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ Superset    │  │ Tableau     │  │ Database    │  │ GitHub      │   │
│  │ MCP Server  │  │ MCP Server  │  │ MCP Server  │  │ MCP Server  │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
│                                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ Filesystem  │  │ n8n         │  │ Slack       │  │ Custom      │   │
│  │ MCP Server  │  │ MCP Server  │  │ MCP Server  │  │ MCP Servers │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     BACKEND INTEGRATION LAYER                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ PostgreSQL  │  │ Redis       │  │ S3/MinIO    │  │ External    │   │
│  │ (Metadata)  │  │ (Cache)     │  │ (Files)     │  │ APIs        │   │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

## 1.2 MCP Server Implementation

### Transport Protocol Selection

Per the [November 2025 MCP Specification](https://modelcontextprotocol.io/specification/2025-11-25):

| Transport | Use Case | Status |
|-----------|----------|--------|
| **stdio** | Local CLI tools, desktop apps | Supported (max compatibility) |
| **Streamable HTTP** | Networked, horizontally scalable | Recommended for production |
| ~~SSE~~ | Deprecated | Use Streamable HTTP instead |

**Recommendation**: Implement Streamable HTTP for `mcp.insightpulseai.net` with stdio fallback for local development.

### Core MCP Server Structure

```python
# mcp_server/main.py
from mcp import Server, Tool, Resource, Prompt
from mcp.transports import StreamableHTTPTransport
import asyncio

class InsightPulseMCPServer:
    """
    Central MCP Gateway for InsightPulse AI platform.
    Aggregates tools from multiple backend services.
    """

    def __init__(self):
        self.server = Server("insightpulse-mcp")
        self._register_tools()
        self._register_resources()
        self._register_prompts()

    def _register_tools(self):
        """Register all available tools."""

        # Superset Tools
        @self.server.tool("superset_query")
        async def superset_query(
            query: str,
            database_id: int = 1
        ) -> dict:
            """Execute SQL query on Superset database."""
            # Implementation

        @self.server.tool("superset_list_dashboards")
        async def superset_list_dashboards() -> list:
            """List all available Superset dashboards."""
            # Implementation

        @self.server.tool("superset_get_chart_data")
        async def superset_get_chart_data(chart_id: int) -> dict:
            """Fetch data from a specific Superset chart."""
            # Implementation

        # n8n Tools
        @self.server.tool("n8n_trigger_workflow")
        async def n8n_trigger_workflow(
            workflow_id: str,
            payload: dict = None
        ) -> dict:
            """Trigger an n8n workflow execution."""
            # Implementation

        @self.server.tool("n8n_list_workflows")
        async def n8n_list_workflows() -> list:
            """List all n8n workflows."""
            # Implementation

        # Tableau Tools (via langchain-tableau)
        @self.server.tool("tableau_query")
        async def tableau_query(
            datasource_luid: str,
            query: str
        ) -> dict:
            """Query Tableau datasource using natural language."""
            # Implementation

        # GitHub Tools
        @self.server.tool("github_search_code")
        async def github_search_code(
            query: str,
            repo: str = None
        ) -> list:
            """Search code in GitHub repositories."""
            # Implementation

    def _register_resources(self):
        """Register available resources."""

        @self.server.resource("superset://dashboards")
        async def get_dashboards():
            """Access Superset dashboards as resources."""
            # Implementation

        @self.server.resource("n8n://workflows")
        async def get_workflows():
            """Access n8n workflows as resources."""
            # Implementation

    def _register_prompts(self):
        """Register prompt templates."""

        @self.server.prompt("analyze_dashboard")
        async def analyze_dashboard_prompt(dashboard_id: int):
            """Prompt for analyzing a Superset dashboard."""
            return f"""
            Analyze the dashboard with ID {dashboard_id}.
            Provide insights on:
            1. Key metrics and trends
            2. Anomalies or outliers
            3. Actionable recommendations
            """

    async def run(self, host: str = "0.0.0.0", port: int = 8080):
        """Start the MCP server."""
        transport = StreamableHTTPTransport(host=host, port=port)
        await self.server.run(transport)


if __name__ == "__main__":
    server = InsightPulseMCPServer()
    asyncio.run(server.run())
```

### Directory Structure

```
mcp.insightpulseai.net/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── mcp_server/
│   ├── __init__.py
│   ├── main.py                 # Main server entry
│   ├── config.py               # Configuration
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── oauth.py            # OAuth 2.0 implementation
│   │   └── jwt.py              # JWT validation
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── superset.py         # Superset integration tools
│   │   ├── n8n.py              # n8n integration tools
│   │   ├── tableau.py          # Tableau integration tools
│   │   ├── github.py           # GitHub integration tools
│   │   └── filesystem.py       # Filesystem tools
│   ├── resources/
│   │   ├── __init__.py
│   │   ├── dashboards.py       # Dashboard resources
│   │   └── workflows.py        # Workflow resources
│   ├── prompts/
│   │   ├── __init__.py
│   │   └── templates.py        # Prompt templates
│   └── middleware/
│       ├── __init__.py
│       ├── rate_limit.py       # Rate limiting
│       ├── logging.py          # Request logging
│       └── metrics.py          # Prometheus metrics
├── tests/
│   └── ...
└── infra/
    ├── do/
    │   └── mcp-app.yaml        # DigitalOcean spec
    └── k8s/
        └── ...                 # Kubernetes manifests
```

## 1.3 Security Implementation

### Authentication (OAuth 2.0 Resource Server)

Per [MCP Authorization Spec (June 2025)](https://thenewstack.io/15-best-practices-for-building-mcp-servers-in-production/):

```python
# mcp_server/auth/oauth.py
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
import jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

ALLOWED_AUDIENCES = ["mcp.insightpulseai.net"]
ALLOWED_ISSUERS = ["https://auth.insightpulseai.net"]

async def verify_token(token: str = Depends(oauth2_scheme)):
    """Verify OAuth 2.0 access token (RFC 8707 Resource Indicators)."""
    try:
        payload = jwt.decode(
            token,
            options={"verify_signature": True},
            audience=ALLOWED_AUDIENCES,
            issuer=ALLOWED_ISSUERS
        )
        return payload
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


async def require_scope(required_scopes: list[str]):
    """Middleware to require specific OAuth scopes."""
    async def check_scopes(token_payload: dict = Depends(verify_token)):
        token_scopes = token_payload.get("scope", "").split()
        if not all(s in token_scopes for s in required_scopes):
            raise HTTPException(status_code=403, detail="Insufficient scope")
        return token_payload
    return check_scopes
```

### Rate Limiting

```python
# mcp_server/middleware/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Apply to MCP endpoints
@limiter.limit("100/minute")  # Per client
@limiter.limit("1000/hour")   # Hourly cap
async def mcp_endpoint(request):
    ...
```

### Idempotency (Critical for Agent Retries)

```python
# mcp_server/middleware/idempotency.py
import hashlib
from redis import Redis

redis = Redis.from_url(os.environ["REDIS_URL"])

async def ensure_idempotent(request_id: str, handler):
    """
    Ensure tool calls are idempotent.
    Agents may retry or parallelize requests.
    """
    cache_key = f"mcp:idempotent:{request_id}"

    # Check cache
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    # Execute and cache
    result = await handler()
    await redis.setex(cache_key, 3600, json.dumps(result))  # 1 hour TTL
    return result
```

## 1.4 Available Tools Summary

| Tool | Description | Scope Required |
|------|-------------|----------------|
| `superset_query` | Execute SQL queries | `superset:read` |
| `superset_list_dashboards` | List dashboards | `superset:read` |
| `superset_get_chart_data` | Fetch chart data | `superset:read` |
| `superset_create_chart` | Create new chart | `superset:write` |
| `n8n_trigger_workflow` | Trigger workflow | `n8n:execute` |
| `n8n_list_workflows` | List workflows | `n8n:read` |
| `n8n_get_execution` | Get execution status | `n8n:read` |
| `tableau_query` | Query datasource | `tableau:read` |
| `tableau_search` | Search datasources | `tableau:read` |
| `github_search_code` | Search code | `github:read` |
| `github_create_pr` | Create pull request | `github:write` |
| `filesystem_read` | Read files | `fs:read` |
| `filesystem_write` | Write files | `fs:write` |

---

# 2. n8n Design (n8n.insightpulseai.net)

## 2.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        INGRESS LAYER                                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Traefik Ingress Controller                    │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │   │
│  │  │ SSL/TLS      │  │ Rate Limit   │  │ OAuth2 Proxy           │ │   │
│  │  │ Termination  │  │              │  │ (Google/GitHub SSO)    │ │   │
│  │  └──────────────┘  └──────────────┘  └────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│   n8n Main    │       │   n8n Webhook │       │   n8n Worker  │
│   (Editor)    │       │   Processor   │       │   Pool        │
│               │       │               │       │               │
│  Port: 5678   │       │  Port: 5679   │       │  Replicas: 3  │
└───────┬───────┘       └───────┬───────┘       └───────┬───────┘
        │                       │                       │
        └───────────────────────┼───────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        DATA LAYER                                        │
│  ┌─────────────────────┐  ┌─────────────────────┐                       │
│  │     PostgreSQL      │  │       Redis         │                       │
│  │   (Workflow Data)   │  │   (Queue + Cache)   │                       │
│  │                     │  │                     │                       │
│  │  - Workflows        │  │  - Job Queue        │                       │
│  │  - Executions       │  │  - Session Cache    │                       │
│  │  - Credentials      │  │  - Rate Limits      │                       │
│  └─────────────────────┘  └─────────────────────┘                       │
└─────────────────────────────────────────────────────────────────────────┘
```

## 2.2 Queue Mode Configuration (Required for Production)

```yaml
# docker-compose.yml
version: "3.8"

services:
  # Main n8n instance (Editor UI)
  n8n-main:
    image: n8nio/n8n:latest
    environment:
      - N8N_HOST=n8n.insightpulseai.net
      - N8N_PROTOCOL=https
      - N8N_PORT=5678
      - WEBHOOK_URL=https://n8n.insightpulseai.net/
      - GENERIC_TIMEZONE=UTC

      # Database (PostgreSQL required for production)
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_DATABASE=n8n
      - DB_POSTGRESDB_USER=${N8N_DB_USER}
      - DB_POSTGRESDB_PASSWORD=${N8N_DB_PASSWORD}

      # Queue Mode (Redis)
      - EXECUTIONS_MODE=queue
      - QUEUE_BULL_REDIS_HOST=redis
      - QUEUE_BULL_REDIS_PORT=6379
      - QUEUE_HEALTH_CHECK_ACTIVE=true

      # Security
      - N8N_BASIC_AUTH_ACTIVE=false  # Use OAuth instead
      - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}

      # Execution settings
      - EXECUTIONS_DATA_SAVE_ON_ERROR=all
      - EXECUTIONS_DATA_SAVE_ON_SUCCESS=all
      - EXECUTIONS_DATA_SAVE_MANUAL_EXECUTIONS=true
      - EXECUTIONS_DATA_PRUNE=true
      - EXECUTIONS_DATA_MAX_AGE=168  # 7 days

    ports:
      - "5678:5678"
    depends_on:
      - postgres
      - redis
    volumes:
      - n8n_data:/home/node/.n8n
    restart: unless-stopped

  # Webhook processor (dedicated for high-throughput)
  n8n-webhook:
    image: n8nio/n8n:latest
    command: webhook
    environment:
      - N8N_HOST=n8n.insightpulseai.net
      - WEBHOOK_URL=https://n8n.insightpulseai.net/
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_DATABASE=n8n
      - DB_POSTGRESDB_USER=${N8N_DB_USER}
      - DB_POSTGRESDB_PASSWORD=${N8N_DB_PASSWORD}
      - EXECUTIONS_MODE=queue
      - QUEUE_BULL_REDIS_HOST=redis
      - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}
    ports:
      - "5679:5678"
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  # Worker pool (scale horizontally)
  n8n-worker:
    image: n8nio/n8n:latest
    command: worker
    environment:
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_DATABASE=n8n
      - DB_POSTGRESDB_USER=${N8N_DB_USER}
      - DB_POSTGRESDB_PASSWORD=${N8N_DB_PASSWORD}
      - EXECUTIONS_MODE=queue
      - QUEUE_BULL_REDIS_HOST=redis
      - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 512M
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=n8n
      - POSTGRES_USER=${N8N_DB_USER}
      - POSTGRES_PASSWORD=${N8N_DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  n8n_data:
  postgres_data:
  redis_data:
```

## 2.3 Key Workflows to Implement

### Workflow 1: MCP Tool Executor

```json
{
  "name": "MCP Tool Executor",
  "nodes": [
    {
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "mcp/execute",
        "httpMethod": "POST",
        "authentication": "headerAuth"
      }
    },
    {
      "name": "Route Tool",
      "type": "n8n-nodes-base.switch",
      "parameters": {
        "rules": [
          {"value": "superset_query", "output": 0},
          {"value": "tableau_query", "output": 1},
          {"value": "github_action", "output": 2}
        ]
      }
    },
    {
      "name": "Execute Superset",
      "type": "n8n-nodes-base.httpRequest"
    },
    {
      "name": "Execute Tableau",
      "type": "n8n-nodes-base.httpRequest"
    },
    {
      "name": "Execute GitHub",
      "type": "n8n-nodes-base.github"
    }
  ]
}
```

### Workflow 2: Dashboard Alert Pipeline

```json
{
  "name": "Superset Alert Pipeline",
  "nodes": [
    {
      "name": "Schedule",
      "type": "n8n-nodes-base.scheduleTrigger",
      "parameters": {
        "rule": {"interval": [{"field": "minutes", "minutesInterval": 15}]}
      }
    },
    {
      "name": "Query Superset",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "https://superset.insightpulseai.net/api/v1/chart/data",
        "method": "POST"
      }
    },
    {
      "name": "Check Thresholds",
      "type": "n8n-nodes-base.if",
      "parameters": {
        "conditions": {
          "number": [{"value1": "={{$json.value}}", "operation": "larger", "value2": 1000}]
        }
      }
    },
    {
      "name": "Send Slack Alert",
      "type": "n8n-nodes-base.slack",
      "parameters": {
        "channel": "#alerts",
        "text": "Alert: Value exceeded threshold"
      }
    }
  ]
}
```

### Workflow 3: Data Sync Pipeline (Tableau → Superset)

```json
{
  "name": "Tableau to Superset Sync",
  "nodes": [
    {
      "name": "Schedule",
      "type": "n8n-nodes-base.scheduleTrigger",
      "parameters": {
        "rule": {"interval": [{"field": "hours", "hoursInterval": 6}]}
      }
    },
    {
      "name": "Query Tableau",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "={{$env.TABLEAU_DOMAIN}}/api/3.22/sites/{{$env.TABLEAU_SITE}}/datasources/{{$json.datasource_luid}}/data"
      }
    },
    {
      "name": "Transform Data",
      "type": "n8n-nodes-base.code",
      "parameters": {
        "jsCode": "return items.map(item => ({ json: transformRow(item.json) }))"
      }
    },
    {
      "name": "Load to Superset DB",
      "type": "n8n-nodes-base.postgres",
      "parameters": {
        "operation": "insert",
        "table": "tableau_synced_data"
      }
    },
    {
      "name": "Refresh Superset Dataset",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "https://superset.insightpulseai.net/api/v1/dataset/{{datasetId}}/refresh"
      }
    }
  ]
}
```

## 2.4 n8n MCP Server Integration

Create an MCP server that exposes n8n capabilities:

```python
# mcp_server/tools/n8n.py
import httpx
import os
from mcp import Tool

N8N_URL = os.environ.get("N8N_URL", "https://n8n.insightpulseai.net")
N8N_API_KEY = os.environ.get("N8N_API_KEY")

headers = {"X-N8N-API-KEY": N8N_API_KEY}


@Tool("n8n_list_workflows")
async def list_workflows() -> list:
    """List all n8n workflows."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{N8N_URL}/api/v1/workflows",
            headers=headers
        )
        return resp.json()["data"]


@Tool("n8n_trigger_workflow")
async def trigger_workflow(
    workflow_id: str,
    payload: dict = None
) -> dict:
    """
    Trigger an n8n workflow execution.

    Args:
        workflow_id: The workflow ID to trigger
        payload: Optional JSON payload to pass to the workflow

    Returns:
        Execution result with status and data
    """
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{N8N_URL}/api/v1/workflows/{workflow_id}/activate",
            headers=headers,
            json=payload or {}
        )
        return resp.json()


@Tool("n8n_get_execution")
async def get_execution(execution_id: str) -> dict:
    """Get the status of a workflow execution."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{N8N_URL}/api/v1/executions/{execution_id}",
            headers=headers
        )
        return resp.json()


@Tool("n8n_execute_webhook")
async def execute_webhook(
    webhook_path: str,
    method: str = "POST",
    payload: dict = None
) -> dict:
    """
    Execute an n8n webhook directly.

    Args:
        webhook_path: Path of the webhook (e.g., "mcp/execute")
        method: HTTP method (GET, POST, etc.)
        payload: JSON payload for POST requests

    Returns:
        Webhook response
    """
    url = f"{N8N_URL}/webhook/{webhook_path}"
    async with httpx.AsyncClient() as client:
        if method == "GET":
            resp = await client.get(url)
        else:
            resp = await client.post(url, json=payload or {})
        return resp.json()
```

---

# 3. Integration Architecture

## 3.1 Full Platform Integration

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AI AGENT CLIENTS                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ Claude Code │  │   Codex     │  │  Custom AI  │  │  MS Agent   │   │
│  │             │  │             │  │   Agents    │  │  Framework  │   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘   │
└─────────┼────────────────┼────────────────┼────────────────┼──────────┘
          │                │                │                │
          └────────────────┴────────────────┴────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    MCP GATEWAY                                           │
│                 mcp.insightpulseai.net                                  │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Tools: superset_*, n8n_*, tableau_*, github_*, filesystem_*    │   │
│  │  Resources: dashboards, workflows, datasources, repositories    │   │
│  │  Prompts: analyze_dashboard, generate_report, debug_workflow    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│   Superset    │       │     n8n       │       │   Tableau     │
│BI Dashboards  │◄─────►│  Workflows    │◄─────►│  Analytics    │
│               │       │               │       │               │
│ superset.     │       │ n8n.          │       │ (External)    │
│ insightpulse  │       │ insightpulse  │       │               │
│ ai.net        │       │ ai.net        │       │               │
└───────┬───────┘       └───────┬───────┘       └───────────────┘
        │                       │
        └───────────┬───────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │      PostgreSQL       │
        │   (Shared Data)       │
        └───────────────────────┘
```

## 3.2 Client Configuration

### Claude Code (.mcp.json)

```json
{
  "mcpServers": {
    "insightpulse": {
      "transport": "http",
      "url": "https://mcp.insightpulseai.net/mcp",
      "headers": {
        "Authorization": "Bearer ${INSIGHTPULSE_MCP_TOKEN}"
      }
    }
  }
}
```

### Codex (config.toml)

```toml
[mcp_servers.insightpulse]
type = "http"
url = "https://mcp.insightpulseai.net/mcp"
api_key_env_var = "INSIGHTPULSE_MCP_TOKEN"
```

### Microsoft Agent Framework

```python
from agent_framework import Agent, Tool
from agent_framework.mcp import MCPClient

# Connect to InsightPulse MCP
mcp_client = MCPClient(
    url="https://mcp.insightpulseai.net/mcp",
    auth_token=os.environ["INSIGHTPULSE_MCP_TOKEN"]
)

# Create agent with MCP tools
agent = Agent(
    name="InsightPulse Agent",
    tools=mcp_client.get_tools(),
    model="gpt-4o"
)

# Execute
result = await agent.run("Analyze the sales dashboard and identify trends")
```

---

# 4. Deployment Specifications

## 4.1 DigitalOcean App Platform

### MCP Server (mcp-app.yaml)

```yaml
name: insightpulse-mcp
region: sfo
services:
  - name: mcp-server
    github:
      repo: jgtolentino/insightpulse-mcp
      branch: main
      deploy_on_push: true
    dockerfile_path: Dockerfile
    instance_size_slug: professional-xs
    instance_count: 2
    http_port: 8080
    health_check:
      http_path: /health
      initial_delay_seconds: 10
      period_seconds: 30
    envs:
      - key: REDIS_URL
        scope: RUN_TIME
        value: ${redis.REDIS_URL}
      - key: DATABASE_URL
        scope: RUN_TIME
        value: ${db.DATABASE_URL}
      - key: SUPERSET_URL
        scope: RUN_TIME
        value: https://superset.insightpulseai.net
      - key: N8N_URL
        scope: RUN_TIME
        value: https://n8n.insightpulseai.net
      - key: OAUTH_ISSUER
        scope: RUN_TIME
        value: https://auth.insightpulseai.net
    cors:
      allow_origins:
        - prefix: "https://insightpulseai.net"
      allow_methods:
        - GET
        - POST
        - OPTIONS
      allow_headers:
        - Authorization
        - Content-Type

databases:
  - name: db
    engine: PG
    version: "15"
    size: db-s-1vcpu-1gb
    num_nodes: 1

  - name: redis
    engine: REDIS
    version: "7"
    size: db-s-1vcpu-1gb
    num_nodes: 1

domains:
  - domain: mcp.insightpulseai.net
    type: PRIMARY
```

### n8n (n8n-app.yaml)

```yaml
name: insightpulse-n8n
region: sfo
services:
  - name: n8n-main
    image:
      registry_type: DOCKER_HUB
      registry: n8nio
      repository: n8n
      tag: latest
    instance_size_slug: professional-s
    instance_count: 1
    http_port: 5678
    health_check:
      http_path: /healthz
    envs:
      - key: N8N_HOST
        value: n8n.insightpulseai.net
      - key: N8N_PROTOCOL
        value: https
      - key: WEBHOOK_URL
        value: https://n8n.insightpulseai.net/
      - key: DB_TYPE
        value: postgresdb
      - key: DB_POSTGRESDB_HOST
        value: ${db.HOSTNAME}
      - key: DB_POSTGRESDB_DATABASE
        value: ${db.DATABASE}
      - key: DB_POSTGRESDB_USER
        value: ${db.USERNAME}
      - key: DB_POSTGRESDB_PASSWORD
        value: ${db.PASSWORD}
      - key: EXECUTIONS_MODE
        value: queue
      - key: QUEUE_BULL_REDIS_HOST
        value: ${redis.HOSTNAME}
      - key: N8N_ENCRYPTION_KEY
        type: SECRET
        value: ${N8N_ENCRYPTION_KEY}

  - name: n8n-worker
    image:
      registry_type: DOCKER_HUB
      registry: n8nio
      repository: n8n
      tag: latest
    instance_size_slug: professional-xs
    instance_count: 2
    run_command: n8n worker
    envs:
      # Same as n8n-main minus http_port

databases:
  - name: db
    engine: PG
    version: "15"
    size: db-s-2vcpu-4gb

  - name: redis
    engine: REDIS
    version: "7"
    size: db-s-1vcpu-2gb

domains:
  - domain: n8n.insightpulseai.net
    type: PRIMARY
```

## 4.2 Environment Variables Summary

| Variable | Service | Description |
|----------|---------|-------------|
| `INSIGHTPULSE_MCP_TOKEN` | Clients | MCP authentication token |
| `OAUTH_ISSUER` | MCP | OAuth 2.0 issuer URL |
| `OAUTH_CLIENT_ID` | MCP | OAuth client ID |
| `OAUTH_CLIENT_SECRET` | MCP | OAuth client secret |
| `SUPERSET_URL` | MCP | Superset instance URL |
| `SUPERSET_API_TOKEN` | MCP | Superset API access token |
| `N8N_URL` | MCP | n8n instance URL |
| `N8N_API_KEY` | MCP | n8n API key |
| `TABLEAU_DOMAIN` | MCP | Tableau Cloud/Server URL |
| `TABLEAU_JWT_*` | MCP | Tableau Connected App creds |
| `N8N_ENCRYPTION_KEY` | n8n | Credential encryption key |
| `N8N_DB_*` | n8n | PostgreSQL credentials |

---

# 5. Monitoring & Observability

## 5.1 Metrics (Prometheus)

```python
# mcp_server/middleware/metrics.py
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
REQUEST_COUNT = Counter(
    'mcp_requests_total',
    'Total MCP requests',
    ['tool', 'status']
)

REQUEST_LATENCY = Histogram(
    'mcp_request_latency_seconds',
    'MCP request latency',
    ['tool']
)

TOOL_ERRORS = Counter(
    'mcp_tool_errors_total',
    'Total tool execution errors',
    ['tool', 'error_type']
)


# Middleware
async def metrics_middleware(request, call_next):
    tool = request.path_params.get("tool", "unknown")

    with REQUEST_LATENCY.labels(tool=tool).time():
        response = await call_next(request)

    REQUEST_COUNT.labels(
        tool=tool,
        status=response.status_code
    ).inc()

    return response
```

## 5.2 Logging (Structured)

```python
# mcp_server/middleware/logging.py
import structlog
from opentelemetry import trace

logger = structlog.get_logger()
tracer = trace.get_tracer(__name__)


async def logging_middleware(request, call_next):
    with tracer.start_as_current_span("mcp_request") as span:
        request_id = request.headers.get("X-Request-ID", str(uuid4()))

        span.set_attribute("request.id", request_id)
        span.set_attribute("request.tool", request.path_params.get("tool"))

        logger.info(
            "mcp_request_started",
            request_id=request_id,
            tool=request.path_params.get("tool"),
            client_ip=request.client.host
        )

        response = await call_next(request)

        logger.info(
            "mcp_request_completed",
            request_id=request_id,
            status=response.status_code,
            duration_ms=span.end_time - span.start_time
        )

        return response
```

## 5.3 Grafana Dashboards

Create dashboards for:

1. **MCP Server Health**
   - Request rate (RPM)
   - Latency percentiles (p50, p95, p99)
   - Error rate by tool
   - Active connections

2. **n8n Workflow Health**
   - Execution count by workflow
   - Success/failure rates
   - Queue depth
   - Worker utilization

3. **Integration Health**
   - Superset API latency
   - Tableau query performance
   - GitHub API rate limits
   - Redis queue metrics

---

# 6. Security Checklist

## MCP Server

- [ ] OAuth 2.0 authentication enabled
- [ ] Rate limiting configured (100/min per client)
- [ ] TLS 1.3 enforced
- [ ] CORS restricted to allowed origins
- [ ] Idempotency keys for state-changing operations
- [ ] Input validation on all tool parameters
- [ ] Audit logging enabled
- [ ] Secrets in environment variables (not code)
- [ ] Network isolation (VPC)
- [ ] Regular security scanning (Snyk, Trivy)

## n8n

- [ ] OAuth/SSO authentication (not basic auth)
- [ ] Encryption key set and rotated
- [ ] PostgreSQL (not SQLite)
- [ ] Webhook URLs secured with auth headers
- [ ] Credential encryption enabled
- [ ] Execution data pruning configured
- [ ] Network isolation (VPC)
- [ ] Regular backups enabled
- [ ] Audit logging for sensitive workflows

---

# 7. Resources

## MCP
- [MCP Specification (Nov 2025)](https://modelcontextprotocol.io/specification/2025-11-25)
- [MCP Best Practices](https://modelcontextprotocol.info/docs/best-practices/)
- [15 Best Practices for MCP Servers](https://thenewstack.io/15-best-practices-for-building-mcp-servers-in-production/)
- [MCP Deep Dive - Deployment](https://abvijaykumar.medium.com/model-context-protocol-deep-dive-part-3-2-3-hands-on-deployment-patterns-3c2c45e65efb)

## n8n
- [n8n Production Deployment](https://www.wednesday.is/writing-articles/n8n-deployment-production-environment-setup)
- [n8n Self-Hosted Guide 2025](https://latenode.com/blog/low-code-no-code-platforms/self-hosted-automation-platforms/how-to-self-host-n8n-complete-setup-guide-production-deployment-checklist-2025)
- [n8n Deployment Docs](https://docs.n8n.io/embed/deployment/)
- [n8n Helm Chart](https://community-charts.github.io/docs/charts/n8n/usage)

## Microsoft Agent Framework
- [GitHub Repository](https://github.com/microsoft/agent-framework)
