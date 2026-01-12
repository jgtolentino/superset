---
name: "tableau-langchain"
description: "Query Tableau Published Datasources using natural language via LangChain integration"
version: "1.0.0"
---

# Tableau LangChain Skill

Query Tableau Published Datasources using natural language through the VizQL Data Service API.

## When to Use

Invoke this skill when:
- Querying Tableau datasources with natural language
- Building agents that access Tableau analytics
- Creating pipelines between Tableau and other BI tools (Superset)
- Searching for available datasources on Tableau Server/Cloud

## Required Environment Variables

```bash
TABLEAU_DOMAIN          # https://your-site.online.tableau.com
TABLEAU_SITE            # Site name
TABLEAU_JWT_CLIENT_ID   # Connected App client ID
TABLEAU_JWT_SECRET_ID   # Connected App secret ID
TABLEAU_JWT_SECRET      # Connected App secret value
TABLEAU_USER            # User email
TABLEAU_DATASOURCE_LUID # Target datasource (optional)
```

## Installation

```bash
pip install langchain-tableau langchain langgraph langchain-openai
```

## Quick Start

### Query a Datasource

```python
from langchain_tableau.tools import initialize_simple_datasource_qa
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
import os

# Initialize tool
tool = initialize_simple_datasource_qa(
    domain=os.environ['TABLEAU_DOMAIN'],
    site=os.environ['TABLEAU_SITE'],
    jwt_client_id=os.environ['TABLEAU_JWT_CLIENT_ID'],
    jwt_secret_id=os.environ['TABLEAU_JWT_SECRET_ID'],
    jwt_secret=os.environ['TABLEAU_JWT_SECRET'],
    tableau_user=os.environ['TABLEAU_USER'],
    datasource_luid=os.environ['TABLEAU_DATASOURCE_LUID'],
    tooling_llm_model='gpt-4o-mini'
)

# Create agent
agent = create_react_agent(
    ChatOpenAI(model="gpt-4o-mini"),
    tools=[tool]
)

# Query
result = agent.invoke({
    "messages": [("user", "What were total sales by region last quarter?")]
})
```

### Search for Datasources

```python
from langchain_tableau.tools import initialize_search_datasource

search_tool = initialize_search_datasource(
    domain=os.environ['TABLEAU_DOMAIN'],
    site=os.environ['TABLEAU_SITE'],
    jwt_client_id=os.environ['TABLEAU_JWT_CLIENT_ID'],
    jwt_secret_id=os.environ['TABLEAU_JWT_SECRET_ID'],
    jwt_secret=os.environ['TABLEAU_JWT_SECRET'],
    tableau_user=os.environ['TABLEAU_USER']
)

# Find datasources
results = search_tool.invoke("sales data")
```

## Integration Pattern: Tableau to Superset

```python
import pandas as pd
from sqlalchemy import create_engine

# 1. Query Tableau
result = tool.invoke("Get monthly revenue by product")

# 2. Convert to DataFrame
df = pd.DataFrame(result['data'])

# 3. Load to Superset database
engine = create_engine(os.environ['SUPERSET__SQLALCHEMY_DATABASE_URI'])
df.to_sql('tableau_revenue', engine, if_exists='replace')
```

## Security

- VizQL Data Service prevents SQL injection
- JWT authentication via Connected Apps
- Never commit credentials to code

## Resources

- [GitHub](https://github.com/tableau/tableau_langchain)
- [PyPI](https://pypi.org/project/langchain-tableau/)
- [Tableau VDS Docs](https://help.tableau.com/current/api/vizql_data_service/)
