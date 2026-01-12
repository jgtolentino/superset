#!/usr/bin/env python3
"""
Tableau LangChain Query Script

Query Tableau Published Datasources using natural language.

Usage:
    python query_tableau.py "What were total sales by region?"
    python query_tableau.py --datasource LUID "Query here"
    python query_tableau.py --search "Find sales datasources"
"""

import os
import sys
import json
import argparse
from typing import Optional


def get_env_or_fail(name: str) -> str:
    """Get environment variable or exit with error."""
    value = os.environ.get(name)
    if not value:
        print(f"BLOCKED: missing env var {name}")
        sys.exit(1)
    return value


def initialize_tools(datasource_luid: Optional[str] = None):
    """Initialize Tableau LangChain tools."""
    from langchain_tableau.tools import initialize_simple_datasource_qa

    # Get configuration from environment
    config = {
        "domain": get_env_or_fail("TABLEAU_DOMAIN"),
        "site": get_env_or_fail("TABLEAU_SITE"),
        "jwt_client_id": get_env_or_fail("TABLEAU_JWT_CLIENT_ID"),
        "jwt_secret_id": get_env_or_fail("TABLEAU_JWT_SECRET_ID"),
        "jwt_secret": get_env_or_fail("TABLEAU_JWT_SECRET"),
        "tableau_user": get_env_or_fail("TABLEAU_USER"),
        "tableau_api_version": os.environ.get("TABLEAU_API_VERSION", "3.22"),
        "tooling_llm_model": os.environ.get("TABLEAU_LLM_MODEL", "gpt-4o-mini"),
    }

    # Use provided datasource or from environment
    ds_luid = datasource_luid or os.environ.get("TABLEAU_DATASOURCE_LUID")
    if not ds_luid:
        print("BLOCKED: missing datasource LUID (--datasource or TABLEAU_DATASOURCE_LUID)")
        sys.exit(1)

    config["datasource_luid"] = ds_luid

    return initialize_simple_datasource_qa(**config)


def create_agent(tools: list):
    """Create a ReAct agent with Tableau tools."""
    from langgraph.prebuilt import create_react_agent

    # Try OpenAI first, then Anthropic
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
        print("BLOCKED: No LLM configured. Set OPENAI_API_KEY or ANTHROPIC_API_KEY")
        sys.exit(1)

    return create_react_agent(
        llm,
        tools=tools,
        state_modifier=(
            "You are a helpful analytics assistant with access to Tableau data. "
            "Answer questions by querying the available datasources. "
            "Provide clear, concise answers with relevant data."
        )
    )


def query_datasource(query: str, datasource_luid: Optional[str] = None):
    """Query a Tableau datasource."""
    print(f"Initializing Tableau connection...")
    tool = initialize_tools(datasource_luid)

    print(f"Creating agent...")
    agent = create_agent([tool])

    print(f"Executing query: {query}")
    print("-" * 60)

    result = agent.invoke({
        "messages": [("user", query)]
    })

    # Extract the final response
    if "messages" in result:
        for msg in reversed(result["messages"]):
            if hasattr(msg, "content") and msg.content:
                print(msg.content)
                return msg.content

    return result


def search_datasources(query: str):
    """Search for datasources on Tableau Server/Cloud."""
    from langchain_tableau.tools import initialize_search_datasource

    config = {
        "domain": get_env_or_fail("TABLEAU_DOMAIN"),
        "site": get_env_or_fail("TABLEAU_SITE"),
        "jwt_client_id": get_env_or_fail("TABLEAU_JWT_CLIENT_ID"),
        "jwt_secret_id": get_env_or_fail("TABLEAU_JWT_SECRET_ID"),
        "jwt_secret": get_env_or_fail("TABLEAU_JWT_SECRET"),
        "tableau_user": get_env_or_fail("TABLEAU_USER"),
    }

    tool = initialize_search_datasource(**config)
    result = tool.invoke(query)

    print("Search Results:")
    print("-" * 60)
    if isinstance(result, list):
        for ds in result:
            print(f"  - {ds.get('name', 'Unknown')}: {ds.get('luid', 'N/A')}")
    else:
        print(result)

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Query Tableau datasources using natural language"
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="Natural language query"
    )
    parser.add_argument(
        "--datasource", "-d",
        help="Datasource LUID to query"
    )
    parser.add_argument(
        "--search", "-s",
        action="store_true",
        help="Search for datasources instead of querying"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )

    args = parser.parse_args()

    if not args.query:
        parser.print_help()
        sys.exit(1)

    try:
        if args.search:
            result = search_datasources(args.query)
        else:
            result = query_datasource(args.query, args.datasource)

        if args.json:
            print(json.dumps({"result": str(result)}, indent=2))

    except Exception as e:
        print(f"ERROR: {e}")
        if os.environ.get("DEBUG"):
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
