# /tableau - Query Tableau Datasources

Query Tableau Published Datasources using natural language via the LangChain integration.

## Usage

```
/tableau <query>
/tableau --search <search_term>
/tableau --setup
```

## Examples

```
/tableau What were total sales by region last quarter?
/tableau --search Find all sales datasources
/tableau --setup  # Validate environment and install dependencies
```

## Arguments

$ARGUMENTS will be passed as the natural language query.

## Implementation

When this command is invoked:

1. **If --setup**: Run the setup script to validate environment and install dependencies:
   ```bash
   python .claude/skills/tableau-langchain/setup.py
   ```

2. **If --search**: Search for datasources:
   ```bash
   python .claude/skills/tableau-langchain/query_tableau.py --search "$ARGUMENTS"
   ```

3. **Otherwise**: Query the configured datasource:
   ```bash
   python .claude/skills/tableau-langchain/query_tableau.py "$ARGUMENTS"
   ```

## Required Environment Variables

Before using this command, ensure these are set:

- `TABLEAU_DOMAIN` - Your Tableau Cloud/Server URL
- `TABLEAU_SITE` - Site name
- `TABLEAU_JWT_CLIENT_ID` - Connected App client ID
- `TABLEAU_JWT_SECRET_ID` - Connected App secret ID
- `TABLEAU_JWT_SECRET` - Connected App secret value
- `TABLEAU_USER` - User email for authentication
- `TABLEAU_DATASOURCE_LUID` - Target datasource LUID (for queries)

## Integration with Superset

After querying Tableau, you can load results into Superset:

```python
# The query_tableau.py script returns data that can be piped to Superset
python .claude/skills/tableau-langchain/query_tableau.py "query" --json | \
  python scripts/load_to_superset.py
```
