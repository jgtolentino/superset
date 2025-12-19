# MCP Tool Enforcer Skill

> A policy skill that ensures optimal tool selection in Claude Code sessions

## Status: Specification Only

This skill is currently in the specification phase. See `spec/mcp-tool-enforcer-skill/` for complete design documents.

## Purpose

The MCP Tool Enforcer monitors command usage during Claude Code sessions and recommends appropriate MCP or built-in tools over shell commands when better alternatives exist.

## Key Features (Planned)

- **Command Detection**: Identifies shell commands with tool alternatives
- **Tool Comparison**: Shows side-by-side comparison of options
- **Graceful Degradation**: Falls back gracefully when MCP unavailable
- **Non-Blocking Warnings**: Advisory by default, never breaks workflows
- **Configurable**: Enforcement levels from advisory to strict

## Quick Reference

### Tool Alternatives

| Shell Command | Recommended Tool | Benefit |
|---------------|------------------|---------|
| `cat file.txt` | `Read` tool | Structured output, pagination |
| `find . -name "*.py"` | `Glob` tool | Faster, integrated results |
| `grep "pattern" .` | `Grep` tool | Streaming, file type filtering |
| `sed -i 's/a/b/g' file` | `Edit` tool | Atomic, conflict detection |
| `echo "content" > file` | `Write` tool | Encoding, permission handling |

### Enforcement Levels

| Level | Behavior |
|-------|----------|
| `advisory` | Info message, no blocking |
| `warning` | Yellow warning, can proceed |
| `confirmation` | Prompt required |
| `strict` | Block until alternative used |

## Specification Documents

| Document | Description |
|----------|-------------|
| [constitution.md](../../spec/mcp-tool-enforcer-skill/constitution.md) | Core principles and rules |
| [prd.md](../../spec/mcp-tool-enforcer-skill/prd.md) | Product requirements |
| [plan.md](../../spec/mcp-tool-enforcer-skill/plan.md) | Implementation plan |
| [tasks.md](../../spec/mcp-tool-enforcer-skill/tasks.md) | Task checklist |

## Usage (Future)

Once implemented, this skill will be automatically active in Claude Code sessions.

### Configuration

Create `.claude/mcp-enforcer.yml`:

```yaml
version: "1.0"

enforcement:
  level: advisory  # advisory | warning | confirmation | strict
  log_decisions: true
  show_comparisons: true

exclusions:
  commands:
    - "git *"
    - "docker *"
    - "make *"
```

### Environment Overrides

```bash
# Set enforcement level
export MCP_ENFORCER_LEVEL=warning

# Enable logging
export MCP_ENFORCER_LOG=true
```

## Implementation Timeline

| Phase | Duration | Focus |
|-------|----------|-------|
| M1-M2 | 2 weeks | Core detection and integration |
| M3-M4 | 2 weeks | Comparison engine and warnings |
| M5-M6 | 2 weeks | Configuration and analytics |
| M7-M8 | 2 weeks | Testing and launch |

**Total**: 8 weeks

## Contributing

To contribute to this skill:

1. Review the specification documents
2. Propose changes via pull request
3. Follow the task checklist in `tasks.md`
4. Ensure all quality gates pass

## License

Apache-2.0
