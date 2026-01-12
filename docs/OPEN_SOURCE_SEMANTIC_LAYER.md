# Open Source Semantic Layer Architecture
## Tableau-like Patterns Without Tableau

This document describes how to achieve Tableau's semantic layer capabilities using 100% open-source tools.

---

## Recommended Stack

| Layer | Tableau Equivalent | Open Source Alternative |
|-------|-------------------|-------------------------|
| **Semantic Layer** | Tableau Data Model / VizQL | **Cube.js** |
| **Metrics Definition** | Calculated Fields | **dbt MetricFlow** |
| **Visualization** | Tableau Desktop/Server | **Apache Superset** |
| **Data Transformation** | Tableau Prep | **dbt Core** |
| **API Access** | VizQL Data Service | **Cube REST/GraphQL API** |
| **Embedded Analytics** | Tableau Embedded | **Cube + Superset Embedded** |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AI AGENTS / APPLICATIONS                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ Claude Code │  │   Codex     │  │  n8n        │  │  Custom     │   │
│  │             │  │             │  │  Workflows  │  │  Apps       │   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘   │
└─────────┼────────────────┼────────────────┼────────────────┼──────────┘
          │                │                │                │
          └────────────────┴────────────────┴────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        MCP GATEWAY                                       │
│                    mcp.insightpulseai.net                               │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  Tools: cube_query, superset_*, dbt_run, metrics_*              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    SEMANTIC LAYER (Cube.js)                              │
│                    cube.insightpulseai.net                              │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Cube Data Model                               │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐ │   │
│  │  │ Cubes    │  │ Measures │  │ Dimensions│  │ Pre-Aggregations│ │   │
│  │  │ (Facts)  │  │ (KPIs)   │  │ (Attrs)  │  │ (Cache)         │ │   │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  APIs: REST | GraphQL | SQL | AI/LLM                                   │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────────────────────┐
        │                       │                                       │
        ▼                       ▼                                       ▼
┌───────────────────┐   ┌───────────────────┐               ┌───────────────────┐
│     Superset      │   │    dbt Core       │               │    Metabase       │
│   (Dashboards)    │   │  (Transformations)│               │   (Alternative)   │
│                   │   │                   │               │                   │
│ superset.         │   │  + MetricFlow     │               │   (Optional)      │
│ insightpulseai    │   │  (Metrics YAML)   │               │                   │
│ .net              │   │                   │               │                   │
└─────────┬─────────┘   └─────────┬─────────┘               └───────────────────┘
          │                       │
          └───────────┬───────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        DATA WAREHOUSE                                    │
│  ┌─────────────────────┐  ┌─────────────────────┐                       │
│  │     PostgreSQL      │  │      DuckDB         │                       │
│  │   (Primary DW)      │  │   (Local/Dev)       │                       │
│  └─────────────────────┘  └─────────────────────┘                       │
│                                                                         │
│  Or: Snowflake | BigQuery | ClickHouse | Databricks                    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Cube.js - Semantic Layer

### Why Cube.js Replaces Tableau's Data Model

| Tableau Feature | Cube.js Equivalent |
|-----------------|-------------------|
| Data Model (relationships) | Cube joins |
| Calculated Fields | Measures with SQL |
| Parameters | Cube variables |
| LOD Expressions | Pre-aggregations |
| Live/Extract modes | Caching + Pre-aggs |
| Row-level security | Multi-tenant security |
| VizQL Data Service | REST/GraphQL/SQL API |

### Installation

```bash
# Install Cube CLI
npm install -g @cubejs-backend/cli

# Create new project
npx cubejs-cli create cube-semantic-layer -d postgres

# Or with Docker
docker run -d \
  --name cube \
  -p 4000:4000 \
  -e CUBEJS_DB_TYPE=postgres \
  -e CUBEJS_DB_HOST=postgres \
  -e CUBEJS_DB_NAME=warehouse \
  -e CUBEJS_DB_USER=${DB_USER} \
  -e CUBEJS_DB_PASS=${DB_PASS} \
  -e CUBEJS_API_SECRET=${CUBE_API_SECRET} \
  cubejs/cube:latest
```

### Data Model Definition

```javascript
// schema/Orders.js - Cube data model (like Tableau data model)
cube(`Orders`, {
  sql_table: `public.orders`,

  // Relationships (like Tableau joins)
  joins: {
    Customers: {
      relationship: `many_to_one`,
      sql: `${CUBE}.customer_id = ${Customers}.id`
    },
    Products: {
      relationship: `many_to_one`,
      sql: `${CUBE}.product_id = ${Products}.id`
    }
  },

  // Measures (like Tableau calculated fields)
  measures: {
    count: {
      type: `count`
    },
    totalRevenue: {
      sql: `amount`,
      type: `sum`,
      title: `Total Revenue`,
      format: `currency`
    },
    averageOrderValue: {
      sql: `${totalRevenue} / ${count}`,
      type: `number`,
      title: `Average Order Value`
    },
    // Like Tableau LOD: FIXED [Customer] : SUM([Sales])
    customerLifetimeValue: {
      sql: `amount`,
      type: `sum`,
      title: `Customer Lifetime Value`,
      // Rolling window
      rolling_window: {
        trailing: `unbounded`
      }
    }
  },

  // Dimensions (like Tableau dimensions)
  dimensions: {
    id: {
      sql: `id`,
      type: `number`,
      primary_key: true
    },
    status: {
      sql: `status`,
      type: `string`
    },
    createdAt: {
      sql: `created_at`,
      type: `time`
    },
    // Date hierarchy (like Tableau date parts)
    createdAtYear: {
      sql: `DATE_TRUNC('year', ${CUBE}.created_at)`,
      type: `time`
    },
    createdAtMonth: {
      sql: `DATE_TRUNC('month', ${CUBE}.created_at)`,
      type: `time`
    }
  },

  // Pre-aggregations (like Tableau extracts - massive performance boost)
  pre_aggregations: {
    dailyRevenue: {
      measures: [totalRevenue, count],
      dimensions: [status],
      time_dimension: createdAt,
      granularity: `day`,
      refresh_key: {
        every: `1 hour`
      }
    },
    monthlyByCustomer: {
      measures: [totalRevenue, averageOrderValue],
      dimensions: [Customers.segment, Customers.region],
      time_dimension: createdAt,
      granularity: `month`
    }
  },

  // Row-level security (like Tableau row-level security)
  segments: {
    onlyActiveOrders: {
      sql: `${CUBE}.status = 'active'`
    }
  }
});
```

```javascript
// schema/Customers.js
cube(`Customers`, {
  sql_table: `public.customers`,

  measures: {
    count: {
      type: `count`
    },
    totalCustomers: {
      sql: `id`,
      type: `count_distinct`
    }
  },

  dimensions: {
    id: {
      sql: `id`,
      type: `number`,
      primary_key: true
    },
    name: {
      sql: `name`,
      type: `string`
    },
    segment: {
      sql: `segment`,
      type: `string`
    },
    region: {
      sql: `region`,
      type: `string`
    },
    country: {
      sql: `country`,
      type: `string`
    }
  }
});
```

### API Usage (Replaces VizQL Data Service)

```bash
# REST API - Query metrics
curl -X POST https://cube.insightpulseai.net/cubejs-api/v1/load \
  -H "Authorization: Bearer ${CUBE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "measures": ["Orders.totalRevenue", "Orders.count"],
    "dimensions": ["Customers.segment", "Customers.region"],
    "timeDimensions": [{
      "dimension": "Orders.createdAt",
      "dateRange": "last 30 days",
      "granularity": "day"
    }],
    "filters": [{
      "dimension": "Orders.status",
      "operator": "equals",
      "values": ["completed"]
    }]
  }'
```

```graphql
# GraphQL API
query {
  cube {
    orders(
      where: { status: { equals: "completed" } }
      orderBy: { createdAt: desc }
      limit: 100
    ) {
      totalRevenue
      count
      customers {
        segment
        region
      }
      createdAt {
        day
      }
    }
  }
}
```

```sql
-- SQL API (for BI tools like Superset)
SELECT
  customers.segment,
  customers.region,
  MEASURE(orders.total_revenue) as revenue,
  MEASURE(orders.count) as order_count
FROM orders
JOIN customers ON orders.customer_id = customers.id
WHERE orders.created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY 1, 2
ORDER BY revenue DESC
```

### AI/LLM API (New in 2025)

```python
# Use Cube's AI API for natural language queries
import httpx

async def query_cube_ai(question: str) -> dict:
    """Query Cube using natural language (like Tableau Ask Data)."""
    response = await httpx.post(
        "https://cube.insightpulseai.net/cubejs-api/v1/ai",
        headers={"Authorization": f"Bearer {CUBE_API_TOKEN}"},
        json={"question": question}
    )
    return response.json()

# Example
result = await query_cube_ai("What were total sales by region last month?")
# Returns: {"query": {...}, "result": [...], "sql": "..."}
```

---

## 2. dbt + MetricFlow - Metrics Definition

### Why dbt MetricFlow

- **Version controlled metrics** - Metrics defined in Git alongside transformations
- **Single source of truth** - One definition used everywhere
- **Open source** - Apache 2.0 license (as of Coalesce 2025)
- **Integrates with Cube** - Export to Cube schema

### Installation

```bash
pip install dbt-core dbt-postgres dbt-metricflow
```

### Metrics Definition

```yaml
# models/marts/metrics/revenue_metrics.yml
semantic_models:
  - name: orders
    defaults:
      agg_time_dimension: order_date
    description: "Order transactions"
    model: ref('fct_orders')

    entities:
      - name: order_id
        type: primary
      - name: customer_id
        type: foreign
      - name: product_id
        type: foreign

    measures:
      - name: order_total
        agg: sum
        expr: amount
        description: "Sum of order amounts"

      - name: order_count
        agg: count
        expr: order_id
        description: "Count of orders"

      - name: customers_with_orders
        agg: count_distinct
        expr: customer_id

    dimensions:
      - name: order_date
        type: time
        type_params:
          time_granularity: day
      - name: order_status
        type: categorical
      - name: is_first_order
        type: categorical
        expr: "CASE WHEN order_number = 1 THEN 'Yes' ELSE 'No' END"

metrics:
  - name: revenue
    description: "Total revenue from completed orders"
    type: simple
    type_params:
      measure: order_total
    filter: |
      {{ Dimension('order_status') }} = 'completed'

  - name: average_order_value
    description: "Average value per order"
    type: derived
    type_params:
      expr: revenue / order_count
      metrics:
        - revenue
        - order_count

  - name: revenue_growth_mom
    description: "Month-over-month revenue growth"
    type: derived
    type_params:
      expr: (revenue - revenue_prev_month) / revenue_prev_month
      metrics:
        - name: revenue
        - name: revenue
          offset_window: 1 month
          alias: revenue_prev_month

  - name: customer_lifetime_value
    description: "Total revenue per customer"
    type: simple
    type_params:
      measure: order_total
    # Like Tableau LOD FIXED
    type_params:
      window:
        window_groupings:
          - customer_id
```

### Query MetricFlow

```bash
# CLI query
mf query --metrics revenue,order_count \
         --group-by metric_time__month,customer__segment \
         --where "metric_time__month >= '2025-01-01'"

# Generate SQL
mf query --metrics revenue --explain
```

### Export to Cube

```python
# scripts/export_metricflow_to_cube.py
"""Export dbt MetricFlow metrics to Cube.js schema."""

import yaml
from pathlib import Path

def export_metrics_to_cube(metrics_yaml: Path, output_dir: Path):
    """Convert MetricFlow metrics to Cube.js schema."""

    with open(metrics_yaml) as f:
        config = yaml.safe_load(f)

    cube_schema = []

    for semantic_model in config.get('semantic_models', []):
        cube = {
            'name': semantic_model['name'].title(),
            'sql_table': f"${{ref('{semantic_model['model']}')}}" if 'model' in semantic_model else semantic_model.get('table'),
            'measures': {},
            'dimensions': {}
        }

        # Convert measures
        for measure in semantic_model.get('measures', []):
            cube['measures'][measure['name']] = {
                'sql': measure.get('expr', measure['name']),
                'type': measure['agg']
            }

        # Convert dimensions
        for dim in semantic_model.get('dimensions', []):
            cube['dimensions'][dim['name']] = {
                'sql': dim.get('expr', dim['name']),
                'type': 'time' if dim['type'] == 'time' else 'string'
            }

        cube_schema.append(cube)

    # Write Cube.js files
    for cube in cube_schema:
        output_file = output_dir / f"{cube['name']}.js"
        with open(output_file, 'w') as f:
            f.write(generate_cube_js(cube))

    return cube_schema
```

---

## 3. Superset Integration

### Connect Superset to Cube

```python
# superset_config.py
# Add Cube as a database connection

DATABASES = {
    'cube': {
        'sqlalchemy_uri': 'cube://cube.insightpulseai.net:4000/cubejs-api/v1/sql?apiToken=<CUBE_API_TOKEN>',
        'engine_params': {
            'connect_args': {
                'authorization': 'Bearer <CUBE_API_TOKEN>'
            }
        }
    }
}
```

Or use Cube's SQL API directly:

```yaml
# Superset database connection
Database Name: Cube Semantic Layer
SQLAlchemy URI: postgresql://cube:password@cube.insightpulseai.net:5432/cube_store
```

### Create Superset Datasets from Cube

```python
# scripts/sync_cube_to_superset.py
"""Sync Cube.js cubes to Superset datasets."""

import httpx
import os

CUBE_URL = os.environ["CUBE_URL"]
SUPERSET_URL = os.environ["SUPERSET_URL"]

async def sync_cube_to_superset():
    """Create Superset datasets from Cube cubes."""

    # Get Cube metadata
    cube_meta = await httpx.get(
        f"{CUBE_URL}/cubejs-api/v1/meta",
        headers={"Authorization": f"Bearer {os.environ['CUBE_API_TOKEN']}"}
    )
    cubes = cube_meta.json()["cubes"]

    # Login to Superset
    superset_token = await get_superset_token()

    for cube in cubes:
        # Create virtual dataset in Superset
        # Using Cube's SQL API as the source
        sql = f"""
        SELECT
          {', '.join(d['name'] for d in cube['dimensions'])},
          {', '.join(f"MEASURE({m['name']}) as {m['name']}" for m in cube['measures'])}
        FROM {cube['name'].lower()}
        """

        await httpx.post(
            f"{SUPERSET_URL}/api/v1/dataset/",
            headers={"Authorization": f"Bearer {superset_token}"},
            json={
                "database": CUBE_DATABASE_ID,
                "sql": sql,
                "table_name": f"cube_{cube['name'].lower()}"
            }
        )
```

---

## 4. MCP Tools for Semantic Layer

### Cube MCP Tools

```python
# mcp_server/tools/cube.py
"""MCP tools for Cube.js semantic layer."""

import httpx
import os
from mcp import Tool

CUBE_URL = os.environ.get("CUBE_URL", "https://cube.insightpulseai.net")
CUBE_TOKEN = os.environ.get("CUBE_API_TOKEN")

headers = {"Authorization": f"Bearer {CUBE_TOKEN}"}


@Tool("cube_query")
async def cube_query(
    measures: list[str],
    dimensions: list[str] = None,
    time_dimension: str = None,
    date_range: str = "last 30 days",
    filters: list[dict] = None,
    limit: int = 1000
) -> dict:
    """
    Query the Cube.js semantic layer.

    Args:
        measures: List of measures to query (e.g., ["Orders.totalRevenue"])
        dimensions: List of dimensions to group by
        time_dimension: Time dimension for date filtering
        date_range: Date range (e.g., "last 30 days", "this year")
        filters: List of filter objects
        limit: Maximum rows to return

    Returns:
        Query results with data and metadata
    """
    query = {
        "measures": measures,
        "limit": limit
    }

    if dimensions:
        query["dimensions"] = dimensions

    if time_dimension:
        query["timeDimensions"] = [{
            "dimension": time_dimension,
            "dateRange": date_range,
            "granularity": "day"
        }]

    if filters:
        query["filters"] = filters

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CUBE_URL}/cubejs-api/v1/load",
            headers=headers,
            json={"query": query}
        )
        return response.json()


@Tool("cube_ai_query")
async def cube_ai_query(question: str) -> dict:
    """
    Query Cube using natural language.

    Args:
        question: Natural language question about the data

    Returns:
        Query results with generated SQL
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CUBE_URL}/cubejs-api/v1/ai",
            headers=headers,
            json={"question": question}
        )
        return response.json()


@Tool("cube_list_cubes")
async def list_cubes() -> list:
    """List all available cubes and their measures/dimensions."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CUBE_URL}/cubejs-api/v1/meta",
            headers=headers
        )
        return response.json()["cubes"]


@Tool("cube_get_sql")
async def get_generated_sql(
    measures: list[str],
    dimensions: list[str] = None
) -> str:
    """
    Get the SQL that Cube would generate for a query.
    Useful for debugging and understanding the semantic layer.
    """
    query = {"measures": measures}
    if dimensions:
        query["dimensions"] = dimensions

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CUBE_URL}/cubejs-api/v1/sql",
            headers=headers,
            json={"query": query}
        )
        return response.json()["sql"]
```

### dbt/MetricFlow MCP Tools

```python
# mcp_server/tools/dbt.py
"""MCP tools for dbt and MetricFlow."""

import subprocess
import json
from mcp import Tool


@Tool("dbt_run")
async def dbt_run(
    models: list[str] = None,
    full_refresh: bool = False
) -> dict:
    """
    Run dbt models.

    Args:
        models: Specific models to run (or all if None)
        full_refresh: Whether to full refresh incremental models

    Returns:
        dbt run results
    """
    cmd = ["dbt", "run"]

    if models:
        cmd.extend(["--select", " ".join(models)])

    if full_refresh:
        cmd.append("--full-refresh")

    result = subprocess.run(cmd, capture_output=True, text=True)

    return {
        "success": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr
    }


@Tool("metricflow_query")
async def metricflow_query(
    metrics: list[str],
    group_by: list[str] = None,
    where: str = None,
    start_time: str = None,
    end_time: str = None
) -> dict:
    """
    Query dbt MetricFlow metrics.

    Args:
        metrics: List of metric names
        group_by: Dimensions to group by
        where: SQL where clause
        start_time: Start date filter
        end_time: End date filter

    Returns:
        Query results
    """
    cmd = ["mf", "query", "--metrics", ",".join(metrics), "--output", "json"]

    if group_by:
        cmd.extend(["--group-by", ",".join(group_by)])

    if where:
        cmd.extend(["--where", where])

    if start_time:
        cmd.extend(["--start-time", start_time])

    if end_time:
        cmd.extend(["--end-time", end_time])

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        return json.loads(result.stdout)
    else:
        return {"error": result.stderr}


@Tool("metricflow_list_metrics")
async def list_metrics() -> list:
    """List all available MetricFlow metrics."""
    result = subprocess.run(
        ["mf", "list", "metrics", "--output", "json"],
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)
```

---

## 5. Deployment

### Docker Compose (Full Stack)

```yaml
# docker-compose.yml
version: "3.8"

services:
  # Cube.js Semantic Layer
  cube:
    image: cubejs/cube:latest
    ports:
      - "4000:4000"
    environment:
      - CUBEJS_DB_TYPE=postgres
      - CUBEJS_DB_HOST=postgres
      - CUBEJS_DB_NAME=warehouse
      - CUBEJS_DB_USER=${DB_USER}
      - CUBEJS_DB_PASS=${DB_PASS}
      - CUBEJS_API_SECRET=${CUBE_API_SECRET}
      - CUBEJS_DEV_MODE=false
      - CUBEJS_CACHE_AND_QUEUE_DRIVER=redis
      - CUBEJS_REDIS_URL=redis://redis:6379
    volumes:
      - ./cube/schema:/cube/conf/schema
    depends_on:
      - postgres
      - redis

  # Apache Superset
  superset:
    image: apache/superset:latest
    ports:
      - "8088:8088"
    environment:
      - SUPERSET_SECRET_KEY=${SUPERSET_SECRET_KEY}
      - DATABASE_URL=postgresql://${DB_USER}:${DB_PASS}@postgres:5432/superset
    volumes:
      - ./superset/superset_config.py:/app/superset_config.py
    depends_on:
      - postgres
      - redis

  # PostgreSQL (Data Warehouse)
  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASS}
      - POSTGRES_DB=warehouse
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql

  # Redis (Cache)
  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  # MCP Server
  mcp:
    build: ./mcp_server
    ports:
      - "8080:8080"
    environment:
      - CUBE_URL=http://cube:4000
      - CUBE_API_TOKEN=${CUBE_API_SECRET}
      - SUPERSET_URL=http://superset:8088
    depends_on:
      - cube
      - superset

volumes:
  postgres_data:
  redis_data:
```

### DigitalOcean App Platform

```yaml
# do-app-spec.yaml
name: insightpulse-semantic
region: sfo

services:
  - name: cube
    image:
      registry_type: DOCKER_HUB
      registry: cubejs
      repository: cube
      tag: latest
    instance_size_slug: professional-s
    http_port: 4000
    envs:
      - key: CUBEJS_DB_TYPE
        value: postgres
      - key: CUBEJS_DB_HOST
        value: ${db.HOSTNAME}
      - key: CUBEJS_DB_NAME
        value: ${db.DATABASE}
      - key: CUBEJS_DB_USER
        value: ${db.USERNAME}
      - key: CUBEJS_DB_PASS
        value: ${db.PASSWORD}
      - key: CUBEJS_API_SECRET
        type: SECRET
        value: ${CUBE_API_SECRET}

databases:
  - name: db
    engine: PG
    version: "15"
    size: db-s-2vcpu-4gb

domains:
  - domain: cube.insightpulseai.net
    type: PRIMARY
```

---

## 6. Comparison: Tableau vs Open Source Stack

| Capability | Tableau | Open Source (Cube + dbt + Superset) |
|------------|---------|-------------------------------------|
| **Semantic Modeling** | Data Model | Cube.js schema |
| **Metrics Definition** | Calculated Fields | dbt MetricFlow + Cube measures |
| **Caching** | Extracts | Cube pre-aggregations |
| **API Access** | VizQL Data Service | Cube REST/GraphQL/SQL API |
| **Natural Language** | Ask Data | Cube AI API |
| **Row-Level Security** | Tableau RLS | Cube security context |
| **Visualization** | Tableau Desktop | Superset dashboards |
| **Embedded Analytics** | Tableau Embedded | Superset Embedded SDK |
| **Cost** | $70-150/user/month | $0 (self-hosted) |
| **Vendor Lock-in** | High | None |
| **Customization** | Limited | Unlimited |

---

## Resources

- [Cube.js Documentation](https://cube.dev/docs)
- [Cube.js GitHub](https://github.com/cube-js/cube) - 65k+ stars
- [dbt MetricFlow](https://docs.getdbt.com/docs/build/build-metrics-intro)
- [Open Source MetricFlow Announcement](https://www.getdbt.com/blog/open-source-metricflow-governed-metrics)
- [Semantic Layer Architectures (2025)](https://www.typedef.ai/resources/semantic-layer-architectures-explained-warehouse-native-vs-dbt-vs-cube)
- [Apache Superset](https://superset.apache.org/)
