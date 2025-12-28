# Claude Memory Integration for Dashboard Development

> Leveraging [Claude Memory](https://www.anthropic.com/news/memory) for persistent context in dashboard workflows

## Overview

Claude Memory provides persistent context across conversations, stored in transparent Markdown files (CLAUDE.md). This enables:

- **Project-based memory**: Dashboard projects maintain separate context
- **User preferences**: Remembered coding styles, naming conventions
- **Team processes**: Shared workflow knowledge across team members

## Memory Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CLAUDE MEMORY HIERARCHY                                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ~/.claude/CLAUDE.md              ← Global user preferences                 │
│      │                                                                       │
│      ├── project/CLAUDE.md        ← Project-specific context                │
│      │       │                                                               │
│      │       ├── environment       (dev/staging/prod)                       │
│      │       ├── conventions       (naming, SQL style)                      │
│      │       └── recent_work       (last 5 sessions)                        │
│      │                                                                       │
│      └── team/CLAUDE.md           ← Shared team knowledge                   │
│              │                                                               │
│              ├── processes         (PR workflow, deploy gates)              │
│              ├── patterns          (approved chart types, layouts)          │
│              └── constraints       (security, RLS requirements)             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Memory File Templates

### Project Memory (CLAUDE.md)

```markdown
# Dashboard Project: Sales Analytics

## Environment
- **Current**: dev
- **Superset URL**: https://superset.insightpulseai.net
- **Database**: analytics_db / gold schema

## Conventions
- Chart naming: `{domain}_{metric}_{viz_type}` (e.g., `sales_revenue_line`)
- Dashboard slugs: kebab-case (e.g., `sales-overview`)
- SQL style: lowercase keywords, explicit JOINs

## Recent Work
- [2025-01-15] Created revenue trend chart
- [2025-01-14] Fixed RLS for regional managers
- [2025-01-13] Added top products bar chart

## Active Filters
- Date range: Last 30 days (default)
- Region: User's assigned region (RLS)

## Known Issues
- Geo heatmap slow on full dataset (use materialized view)
- ECharts tooltip needs custom formatter for currency
```

### Team Memory (team/CLAUDE.md)

```markdown
# Team: BI Platform

## Deployment Process
1. Create branch from main
2. Edit assets/*.yaml.j2
3. Run `hybrid compile --env dev && hybrid validate`
4. Create PR with `hybrid plan` output
5. After merge: CI runs `hybrid apply --env staging`
6. Manual approval for prod promotion

## Approved Chart Types
| Use Case | Primary | Fallback |
|----------|---------|----------|
| Time series | echarts_timeseries_line | line |
| Distribution | echarts_bar | dist_bar |
| KPI | big_number_total | - |
| Geo | echarts_map | - |

## Security Requirements
- All dashboards must have RLS enabled
- No hardcoded credentials in SQL
- Sensitive filters use `{{ current_user() }}`

## Review Checklist
- [ ] Dataset uses gold schema (not raw)
- [ ] Chart has meaningful title and description
- [ ] RLS clause added for multi-tenant access
- [ ] Tested in dev before PR
```

## Use Cases for Dashboard Development

### 1. Software Engineering (Primary Use Case)

> "Software engineering is the overwhelming favorite use case for Claude" ([Inc.](https://www.inc.com/ben-sherry/anthropics-claude-ai-has-1-killer-use-case-according-to-new-data/91240506))

| Task | Memory Context Used |
|------|---------------------|
| Debug SQL query | Schema, recent errors, query patterns |
| Create chart | Approved viz types, naming conventions |
| Fix RLS issue | Security requirements, user roles |
| Deploy changes | Deployment process, env URLs |

### 2. Code Generation with Context

```python
# Claude remembers from previous sessions:
# - Project uses ECharts-first approach
# - Naming convention: {domain}_{metric}_{viz_type}
# - SQL style: lowercase, explicit JOINs

# So when asked "create a revenue by region chart":
chart_spec = {
    "slice_name": "sales_revenue_by_region_bar",  # Follows convention
    "viz_type": "echarts_bar",  # ECharts-first
    "datasource_name": "gold_transactions",  # Gold schema
    "params": {
        "metrics": ["sum__amount"],
        "groupby": ["region"],
    }
}
```

### 3. Workflow Continuity

```
Session 1:
  User: "Help me create a sales dashboard"
  Claude: Creates initial dashboard spec
  Memory: Saved project context, chosen approach

Session 2 (next day):
  User: "Let's continue with the dashboard"
  Claude: "Last time we created the KPI row and trend line.
           Next up was the top products bar chart. Should I proceed?"
  Memory: Retrieved previous work, current state
```

## Integration with Hybrid Control Plane

### Memory-Aware CLI Wrapper

```python
# src/hybrid/memory.py
from pathlib import Path
import yaml

class ClaudeMemory:
    """Interface with Claude Memory files."""

    def __init__(self, project_root: Path):
        self.root = project_root
        self.memory_file = project_root / "CLAUDE.md"

    def get_context(self) -> dict:
        """Load memory context for Claude."""
        if not self.memory_file.exists():
            return {}

        content = self.memory_file.read_text()
        return self._parse_memory(content)

    def update_recent_work(self, action: str):
        """Add entry to recent work section."""
        from datetime import date
        entry = f"- [{date.today()}] {action}"
        self._append_to_section("Recent Work", entry)

    def get_conventions(self) -> dict:
        """Get naming/style conventions."""
        ctx = self.get_context()
        return ctx.get("conventions", {})

    def get_environment(self) -> str:
        """Get current environment from memory."""
        ctx = self.get_context()
        return ctx.get("environment", {}).get("current", "dev")
```

### Memory-Augmented Commands

```bash
# hybrid CLI reads from CLAUDE.md for context
hybrid compile --env dev
# → Reads conventions from memory
# → Applies naming patterns automatically

hybrid plan --env dev
# → References recent work for change summary
# → Highlights drift from previous session

hybrid apply --env dev
# → Updates "Recent Work" in memory after success
```

## MCP Memory Tool

Expose memory via MCP for agent access:

```typescript
// MCP tool for memory operations
server.setRequestHandler("tools/list", async () => ({
  tools: [
    {
      name: "memory_read",
      description: "Read project or team memory",
      inputSchema: {
        type: "object",
        properties: {
          scope: { type: "string", enum: ["project", "team", "user"] },
          section: { type: "string", description: "Optional section name" }
        }
      }
    },
    {
      name: "memory_update",
      description: "Update memory with new information",
      inputSchema: {
        type: "object",
        properties: {
          scope: { type: "string", enum: ["project", "team"] },
          section: { type: "string" },
          content: { type: "string" }
        },
        required: ["scope", "section", "content"]
      }
    }
  ]
}));
```

## Enterprise Use Case Alignment

Based on [Anthropic's enterprise data](https://www.anthropic.com/news/driving-ai-transformation-with-claude):

| Claude Use Case | Dashboard Application |
|-----------------|----------------------|
| **Software Engineering** (46%) | SQL queries, chart configs, CI/CD |
| **Office/Admin** (10%) | Documentation, reports, emails |
| **Science** (7%) | Data analysis, statistical charts |
| **Business/Finance** (3%) | KPIs, financial dashboards |

## Privacy & Security

> "Memory data is encrypted and treated with the same security as chat content" ([Anthropic](https://www.anthropic.com/news/memory))

| Aspect | Implementation |
|--------|----------------|
| Encryption | At rest and in transit |
| Access control | Per-user, per-project |
| Data residency | Not used for training (paid plans) |
| Export | Portable to other platforms |

## Getting Started

1. **Enable Memory** in Claude settings
2. **Create project CLAUDE.md**:
   ```bash
   cat > CLAUDE.md << 'EOF'
   # Dashboard Project: [Your Project]

   ## Environment
   - **Current**: dev
   - **Superset URL**: [URL]

   ## Conventions
   - Chart naming: {domain}_{metric}_{viz_type}
   - Dashboard slugs: kebab-case
   EOF
   ```
3. **Start a session**: "What were we working on last time?"
4. **Claude remembers**: Previous context loaded automatically

## Resources

- [Claude Memory Announcement](https://www.anthropic.com/news/memory)
- [Memory Tool Documentation](https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool)
- [Enterprise AI Transformation](https://www.anthropic.com/news/driving-ai-transformation-with-claude)
- [How AI Is Transforming Work at Anthropic](https://www.anthropic.com/research/how-ai-is-transforming-work-at-anthropic)
