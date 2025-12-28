# Agent Loop for Ops

Loop:
1) Read current state (latest gh runs, drift plan, dbmate status)
2) Take action (patch workflows / apply assets / migrate DB)
3) Verify (rerun workflow, re-check drift)
4) Repeat until green

## Source References

- Claude Cookbooks: `patterns/agents/` directory
- Claude Cookbooks: `claude_agent_sdk/` directory

## The Loop Pattern

```
┌─────────────────────────────────────────────────────────────────┐
│  1. GATHER CONTEXT                                              │
│     - gh run list --limit 30                                    │
│     - hybrid drift-plan --env <env>                             │
│     - dbmate status                                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. TAKE ACTION                                                 │
│     - Edit workflow YAML                                        │
│     - Run hybrid apply                                          │
│     - Run dbmate up                                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. VERIFY                                                      │
│     - gh run rerun <run_id> --failed                            │
│     - gh run watch <run_id>                                     │
│     - hybrid drift-plan --env <env>                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. REPEAT UNTIL GREEN                                          │
│     - All workflows pass                                        │
│     - No drift detected                                         │
│     - All migrations applied                                    │
└─────────────────────────────────────────────────────────────────┘
```

## Commands

```bash
# List recent workflow runs
gh run list --limit 30

# View failed run logs
gh run view --log-failed <run_id>

# Rerun failed jobs
gh run rerun <run_id> --failed

# Watch a run
gh run watch <run_id>
```

## Decision Tree

```
Is there a failing workflow?
├── YES: Diagnose → Fix → Commit → Rerun → Verify
└── NO: Is there drift?
    ├── YES: Export → PR → Merge → Apply → Verify
    └── NO: DONE (all green)
```

## Applies to

- `scripts/export_to_pr.sh`
- `.github/workflows/ui-export-pr.yml`
