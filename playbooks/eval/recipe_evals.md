# Recipe Evals (Golden Tests)

Each imported pattern becomes a test case:
- Input bundle -> expected plan/apply/drift JSON shapes
- Fail fast on schema changes

## Source References

- Claude Cookbooks: `tool_evaluation/` directory

## Minimal Approach

1. Store sample outputs under `tests/recipes/*.golden.json`
2. Validate in CI with `jq -e` and optional pytest

## Directory Structure

```
tests/
├── recipes/
│   ├── simple_dashboard/
│   │   ├── input/
│   │   │   └── dashboards/example.yaml
│   │   ├── plan.golden.json
│   │   ├── apply.golden.json
│   │   └── drift.golden.json
│   └── multi_chart/
│       ├── input/
│       │   ├── charts/chart1.yaml
│       │   └── charts/chart2.yaml
│       └── plan.golden.json
```

## Golden Test Format

```json
{
  "_meta": {
    "recipe": "simple_dashboard",
    "version": "1.0.0",
    "created": "2024-01-15"
  },
  "expected": {
    "status": "ok",
    "created": 1,
    "updated": 0,
    "errors": []
  },
  "assertions": [
    ".status == 'ok'",
    ".errors | length == 0"
  ]
}
```

## CI Integration

```yaml
# .github/workflows/hybrid.yml
- name: Run recipe evals
  run: |
    for recipe in tests/recipes/*/; do
      echo "Testing: $recipe"
      hybrid plan --env test --input "$recipe/input" | \
        jq -e --slurpfile expected "$recipe/plan.golden.json" \
        '($expected[0].assertions[] | . as $a | input | eval($a)) | all'
    done
```

## Applies to

- `tests/recipes/`
- `.github/workflows/hybrid.yml`
