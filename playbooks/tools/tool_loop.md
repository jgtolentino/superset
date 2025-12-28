# Tool Loop Contract (Control Plane)

This repo treats every operation as a tool-call loop:
1) Gather context (config/env/state)
2) Produce a structured plan (JSON)
3) Execute tools (dbmate, superset-cli/preset-cli, git, gh)
4) Emit structured result (JSON)
5) Verify with deterministic checks; repeat until clean

## Source References

- Claude Cookbooks: `tool_use/` directory
- OpenAI Cookbook: Function Calling guide

## Standard phases

```
compile -> validate -> plan -> apply -> verify -> export(optional) -> PR(optional)
```

## Required outputs

| Command | Output | Schema |
|---------|--------|--------|
| `hybrid plan --json` | manifest + file hashes | `{ env, bundle, files, sha256: {path: hash} }` |
| `hybrid apply --json` | counts + status + errors | `{ env, status, created, updated, errors[] }` |
| `hybrid drift-plan --json` | drift boolean + diff | `{ env, drift, changed_files[], diff_preview }` |

## Required checks (examples)

```bash
# Plan must parse and contain files
hybrid plan --env dev | jq -e .files

# Apply must return status
hybrid apply --env dev --json | jq -e .status

# Drift must be detectable
hybrid drift-plan --env dev --json | jq -e .drift
```

## Implementation Pattern

```python
# Every tool call follows this pattern
def tool_loop(env: str):
    # 1. Gather context
    config = load_config(env)

    # 2. Produce structured plan
    plan = compile_bundle(config)
    validate_plan(plan)

    # 3. Execute tools
    result = apply_bundle(plan)

    # 4. Emit structured result
    emit_json(result)

    # 5. Verify
    drift = check_drift(env)
    if drift:
        raise DriftError(drift)
```

## Applies to

- `src/hybrid/superset.py`
- `src/hybrid/cli.py`
- `scripts/sync_env.sh`
