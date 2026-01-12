#!/usr/bin/env python3
"""
Tableau to Superset Pipeline

Query Tableau datasources and load results into Superset for visualization.

Usage:
    python tableau_to_superset.py "What were sales by region?" --table sales_by_region
    python tableau_to_superset.py --datasource LUID "query" --table table_name
"""

import os
import sys
import json
import argparse
from typing import Optional, Dict, Any
import pandas as pd


def get_env_or_fail(name: str) -> str:
    """Get environment variable or exit with error."""
    value = os.environ.get(name)
    if not value:
        print(f"BLOCKED: missing env var {name}")
        sys.exit(1)
    return value


def query_tableau(query: str, datasource_luid: Optional[str] = None) -> Dict[str, Any]:
    """Query Tableau using LangChain tools."""
    from langchain_tableau.tools import initialize_simple_datasource_qa
    from langgraph.prebuilt import create_react_agent

    # Initialize LLM
    llm = None
    try:
        from langchain_openai import ChatOpenAI
        if os.environ.get("OPENAI_API_KEY"):
            llm = ChatOpenAI(model="gpt-4o-mini")
    except ImportError:
        pass

    if llm is None:
        try:
            from langchain_anthropic import ChatAnthropic
            if os.environ.get("ANTHROPIC_API_KEY"):
                llm = ChatAnthropic(model="claude-3-sonnet-20240229")
        except ImportError:
            pass

    if llm is None:
        raise RuntimeError("No LLM configured. Set OPENAI_API_KEY or ANTHROPIC_API_KEY")

    # Initialize Tableau tool
    ds_luid = datasource_luid or os.environ.get("TABLEAU_DATASOURCE_LUID")
    if not ds_luid:
        raise RuntimeError("Missing datasource LUID")

    tool = initialize_simple_datasource_qa(
        domain=get_env_or_fail("TABLEAU_DOMAIN"),
        site=get_env_or_fail("TABLEAU_SITE"),
        jwt_client_id=get_env_or_fail("TABLEAU_JWT_CLIENT_ID"),
        jwt_secret_id=get_env_or_fail("TABLEAU_JWT_SECRET_ID"),
        jwt_secret=get_env_or_fail("TABLEAU_JWT_SECRET"),
        tableau_user=get_env_or_fail("TABLEAU_USER"),
        tableau_api_version=os.environ.get("TABLEAU_API_VERSION", "3.22"),
        datasource_luid=ds_luid,
        tooling_llm_model=os.environ.get("TABLEAU_LLM_MODEL", "gpt-4o-mini"),
    )

    # Create agent and query
    agent = create_react_agent(
        llm,
        tools=[tool],
        state_modifier="You are a data extraction assistant. Return data in structured format."
    )

    result = agent.invoke({
        "messages": [("user", f"Query and return raw data: {query}")]
    })

    return result


def load_to_superset(
    df: pd.DataFrame,
    table_name: str,
    if_exists: str = "replace"
) -> bool:
    """Load DataFrame to Superset's database."""
    from sqlalchemy import create_engine

    db_uri = get_env_or_fail("SUPERSET__SQLALCHEMY_DATABASE_URI")
    engine = create_engine(db_uri)

    print(f"Loading {len(df)} rows to table '{table_name}'...")
    df.to_sql(table_name, engine, if_exists=if_exists, index=False)
    print(f"Successfully loaded data to '{table_name}'")

    return True


def create_superset_dataset(table_name: str) -> Optional[Dict]:
    """Create a Superset dataset for the loaded table."""
    import requests

    base_url = get_env_or_fail("BASE_URL")
    username = get_env_or_fail("SUPERSET_ADMIN_USER")
    password = get_env_or_fail("SUPERSET_ADMIN_PASS")

    # Login to get access token
    login_url = f"{base_url}/api/v1/security/login"
    login_resp = requests.post(login_url, json={
        "username": username,
        "password": password,
        "provider": "db"
    })

    if login_resp.status_code != 200:
        print(f"WARNING: Could not login to Superset: {login_resp.text}")
        return None

    access_token = login_resp.json().get("access_token")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Get database ID (assuming default database)
    db_resp = requests.get(f"{base_url}/api/v1/database/", headers=headers)
    if db_resp.status_code != 200:
        print(f"WARNING: Could not get databases: {db_resp.text}")
        return None

    databases = db_resp.json().get("result", [])
    if not databases:
        print("WARNING: No databases found in Superset")
        return None

    database_id = databases[0]["id"]

    # Create dataset
    dataset_url = f"{base_url}/api/v1/dataset/"
    dataset_resp = requests.post(dataset_url, headers=headers, json={
        "database": database_id,
        "table_name": table_name,
        "schema": "public"
    })

    if dataset_resp.status_code in [200, 201]:
        print(f"Created Superset dataset for '{table_name}'")
        return dataset_resp.json()
    else:
        print(f"WARNING: Could not create dataset: {dataset_resp.text}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Query Tableau and load results to Superset"
    )
    parser.add_argument(
        "query",
        help="Natural language query for Tableau"
    )
    parser.add_argument(
        "--table", "-t",
        required=True,
        help="Target table name in Superset database"
    )
    parser.add_argument(
        "--datasource", "-d",
        help="Tableau datasource LUID"
    )
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append to existing table instead of replacing"
    )
    parser.add_argument(
        "--create-dataset",
        action="store_true",
        help="Also create a Superset dataset"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )

    args = parser.parse_args()

    try:
        # Step 1: Query Tableau
        print(f"Querying Tableau: {args.query}")
        print("-" * 60)
        result = query_tableau(args.query, args.datasource)

        # Step 2: Convert to DataFrame
        # The result structure depends on the agent's response
        # This is a simplified extraction
        if isinstance(result, dict) and "data" in result:
            df = pd.DataFrame(result["data"])
        elif isinstance(result, dict) and "messages" in result:
            # Extract data from agent messages
            for msg in reversed(result["messages"]):
                if hasattr(msg, "content"):
                    try:
                        data = json.loads(msg.content)
                        if isinstance(data, list):
                            df = pd.DataFrame(data)
                            break
                    except (json.JSONDecodeError, TypeError):
                        continue
            else:
                print("WARNING: Could not extract structured data from response")
                print("Raw response:")
                print(result)
                sys.exit(1)
        else:
            print("WARNING: Unexpected response format")
            print(result)
            sys.exit(1)

        print(f"Extracted {len(df)} rows, {len(df.columns)} columns")
        print(f"Columns: {list(df.columns)}")

        # Step 3: Load to Superset
        if_exists = "append" if args.append else "replace"
        load_to_superset(df, args.table, if_exists)

        # Step 4: Optionally create dataset
        if args.create_dataset:
            create_superset_dataset(args.table)

        # Output summary
        summary = {
            "status": "success",
            "query": args.query,
            "table": args.table,
            "rows": len(df),
            "columns": list(df.columns)
        }

        if args.json:
            print(json.dumps(summary, indent=2))
        else:
            print("\n" + "=" * 60)
            print("Pipeline complete!")
            print(f"  Table: {args.table}")
            print(f"  Rows: {len(df)}")
            print("=" * 60)

    except Exception as e:
        print(f"ERROR: {e}")
        if os.environ.get("DEBUG"):
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
