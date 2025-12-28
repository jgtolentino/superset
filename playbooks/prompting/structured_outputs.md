# Structured Outputs Everywhere

Rule: every agent step and every CLI command emits schema-validated JSON.
No free-form plans. No "logs-only" outputs.

## Source References

- OpenAI Cookbook: Structured Outputs guide
- Claude: JSON mode + tool outputs

## Where enforced

| Command | Output File | Validation |
|---------|-------------|------------|
| `hybrid plan` | `plan.json` | `jq -e .files` |
| `hybrid drift-plan` | `drift.json` | `jq -e .drift` |
| `hybrid apply` | `apply.json` | `jq -e .status` |

## Minimal Schemas (v1)

### Plan Schema

```json
{
  "env": "dev",
  "bundle": "bundles/dev/",
  "files": ["dashboards/sales.yaml", "charts/revenue.yaml"],
  "sha256": {
    "dashboards/sales.yaml": "abc123...",
    "charts/revenue.yaml": "def456..."
  },
  "compiled_at": "2024-01-15T10:30:00Z"
}
```

### Drift Schema

```json
{
  "env": "dev",
  "drift": true,
  "changed_files": ["dashboards/sales.yaml"],
  "diff_preview": "- title: Old\n+ title: New",
  "checked_at": "2024-01-15T10:35:00Z"
}
```

### Apply Schema

```json
{
  "env": "dev",
  "status": "ok",
  "created": 2,
  "updated": 5,
  "deleted": 0,
  "errors": [],
  "applied_at": "2024-01-15T10:40:00Z"
}
```

## CI gates

```bash
# Plan must parse and contain sha256
hybrid plan --env dev | jq -e .sha256

# Apply must contain status
hybrid apply --env dev --json | jq -e '.status == "ok"'

# Drift detection must be boolean
hybrid drift-plan --env dev --json | jq -e '.drift | type == "boolean"'
```

## Applies to

- `src/hybrid/cli.py`
- `scripts/export_to_pr.sh`
- `.github/workflows/hybrid.yml`
