# Cookbook to Hybrid Mapping (generated)

This doc maps external best-practice sources to concrete modules, contracts, and checks in this repo.

## Sources

- **claude_cookbooks**: https://github.com/anthropics/claude-cookbooks
- **openai_cookbook**: https://cookbook.openai.com/

## Mapping Table

| ID | Principle | Playbook | Hybrid Targets | Output Contracts | Checks |
|---|---|---|---|---|---|
| `tool_loop_contract` | Standard tool execution loop (plan -> tool_call -> execute -> report -> verify)<br><sub>claude_cookbooks:tool_use, openai_cookbook:tool_function_calling</sub> | `playbooks/tools/tool_loop.md` | src/hybrid/superset.py<br>src/hybrid/cli.py<br>scripts/sync_env.sh | hybrid apply --json<br>hybrid drift-plan --json | hybrid plan --env dev \| jq -e .<br>hybrid apply --env dev --json \| jq -e .status |
| `structured_outputs_everywhere` | Every agent step and CLI step emits schema-valid JSON (no free-form 'plans')<br><sub>openai_cookbook:structured_outputs</sub> | `playbooks/prompting/structured_outputs.md` | src/hybrid/cli.py<br>scripts/export_to_pr.sh<br>.github/workflows/hybrid.yml | plan.json<br>apply.json<br>drift.json | hybrid plan --env dev \| jq -e .files<br>hybrid drift-plan --env dev --json \| jq -e .drift |
| `observability_and_audit` | Trace every deploy/export/promotion; store manifests; fail on drift unless explicitly overridden<br><sub>claude_cookbooks:observability, claude_cookbooks:tool_evaluation</sub> | `playbooks/observability/observability.md` | scripts/sync_env.sh<br>scripts/export_to_pr.sh<br>docs/spec/**/* |  | test -f .hybrid/deployments/dev/latest.json \|\| true<br>git diff --exit-code docs \|\| true |
| `agent_patterns_for_ops` | Claude Agent SDK Loop: gather context -> take action -> verify -> repeat<br><sub>claude_cookbooks:patterns/agents, claude_cookbooks:claude_agent_sdk</sub> | `playbooks/agent/agent_loop.md` | scripts/export_to_pr.sh<br>.github/workflows/ui-export-pr.yml |  | gh run list --limit 10 |
| `automated_evals_for_recipes` | Turn each 'recipe' into a golden test case (inputs -> expected outputs)<br><sub>claude_cookbooks:tool_evaluation</sub> | `playbooks/eval/recipe_evals.md` | tests/recipes/<br>.github/workflows/hybrid.yml |  | pytest -q \|\| true |
