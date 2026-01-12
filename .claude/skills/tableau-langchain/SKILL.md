# Tableau LangChain Integration Skill

## Overview

This skill enables querying Tableau Published Datasources using natural language through the `langchain-tableau` package. It leverages Tableau's VizQL Data Service (VDS) API for secure, semantic data access.

## When to Use

Use this skill when:
- User asks to query Tableau datasources
- User wants to analyze data from Tableau Cloud/Server
- User needs to build agents that interact with Tableau
- User wants to create BI pipelines combining Tableau + Superset

## Prerequisites

### Environment Variables (Required)

```bash
TABLEAU_DOMAIN          # e.g., https://your-site.online.tableau.com
TABLEAU_SITE            # Site name (not URL)
TABLEAU_JWT_CLIENT_ID   # Connected App client ID
TABLEAU_JWT_SECRET_ID   # Connected App secret ID
TABLEAU_JWT_SECRET      # Connected App secret value
TABLEAU_USER            # User email for authentication
TABLEAU_API_VERSION     # Default: 3.22
```

### Python Dependencies

```bash
pip install langchain-tableau langchain langgraph
```

## Usage Patterns

### 1. Initialize Datasource Q&A Tool

```python
from langchain_tableau.tools import initialize_simple_datasource_qa
import os

# Initialize the tool
tableau_qa_tool = initialize_simple_datasource_qa(
    domain=os.environ['TABLEAU_DOMAIN'],
    site=os.environ['TABLEAU_SITE'],
    jwt_client_id=os.environ['TABLEAU_JWT_CLIENT_ID'],
    jwt_secret_id=os.environ['TABLEAU_JWT_SECRET_ID'],
    jwt_secret=os.environ['TABLEAU_JWT_SECRET'],
    tableau_api_version=os.environ.get('TABLEAU_API_VERSION', '3.22'),
    tableau_user=os.environ['TABLEAU_USER'],
    datasource_luid='YOUR_DATASOURCE_LUID',  # From Tableau
    tooling_llm_model='gpt-4o-mini'  # Or claude-3-sonnet
)
```

### 2. Create ReAct Agent with Tableau Tools

```python
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o-mini")

# Create agent with Tableau tools
agent = create_react_agent(
    llm,
    tools=[tableau_qa_tool],
    state_modifier="You are a helpful analytics assistant with access to Tableau data."
)

# Query the agent
result = agent.invoke({
    "messages": [("user", "What were total sales by region last quarter?")]
})
```

### 3. Multi-Tool Agent (Search + Query)

```python
from langchain_tableau.tools import (
    initialize_simple_datasource_qa,
    initialize_search_datasource
)

# Search tool to find datasources
search_tool = initialize_search_datasource(
    domain=os.environ['TABLEAU_DOMAIN'],
    site=os.environ['TABLEAU_SITE'],
    jwt_client_id=os.environ['TABLEAU_JWT_CLIENT_ID'],
    jwt_secret_id=os.environ['TABLEAU_JWT_SECRET_ID'],
    jwt_secret=os.environ['TABLEAU_JWT_SECRET'],
    tableau_user=os.environ['TABLEAU_USER']
)

# Create agent with both tools
agent = create_react_agent(
    llm,
    tools=[search_tool, tableau_qa_tool],
    state_modifier="You can search for and query Tableau datasources."
)
```

## Integration with Superset

### Pattern: Tableau to Superset Pipeline

```python
import pandas as pd
from sqlalchemy import create_engine

# 1. Query Tableau using LangChain
result = tableau_qa_tool.invoke("Get monthly sales by product category")

# 2. Convert to DataFrame
df = pd.DataFrame(result['data'])

# 3. Load into Superset database
engine = create_engine(os.environ['SUPERSET__SQLALCHEMY_DATABASE_URI'])
df.to_sql('tableau_sales_data', engine, if_exists='replace', index=False)

# 4. Create Superset dataset via API
# (Use existing Superset API scripts)
```

## Security Notes

- VizQL Data Service prevents SQL injection by design
- All queries go through Tableau's API layer
- Connected Apps use JWT for secure authentication
- Never commit credentials to code

## Troubleshooting

### "VizqlDataApiAccess permission denied"
Enable VDS API access for the datasource in Tableau Server/Cloud settings.

### "Invalid JWT"
Check that Connected App credentials match and user has access.

### "Datasource not found"
Verify the datasource LUID is correct (find in Tableau URL or via API).

## Resources

- [Tableau LangChain GitHub](https://github.com/tableau/tableau_langchain)
- [LangChain Tableau Docs](https://python.langchain.com/docs/integrations/tools/tableau/)
- [PyPI Package](https://pypi.org/project/langchain-tableau/)
- [VizQL Data Service Docs](https://help.tableau.com/current/api/vizql_data_service/en-us/)
