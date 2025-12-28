# Context Engineering for Hybrid Control Plane

> Based on [Anthropic's Context Engineering Guide](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)

## Core Principle

> "Context engineering is the delicate art and science of filling the context window with just the right information for the next step."
> — Andrej Karpathy

Context is a **critical but finite resource**. The goal is curating the optimal set of tokens during inference—not just writing better prompts.

---

## Context Engineering vs Prompt Engineering

| Aspect | Prompt Engineering | Context Engineering |
|--------|-------------------|---------------------|
| Focus | Word choice, phrasing | Information architecture |
| Scope | Single prompt | Entire context window |
| Goal | Better instructions | Right information at right time |
| Tokens | Static | Dynamic, curated |

---

## The Five Pillars

### 1. Tool Design (Avoid Bloat)

> "If a human engineer can't definitively say which tool should be used in a given situation, an AI agent can't be expected to do better."

**Anti-pattern:**
```yaml
tools:
  - name: dashboard_operations
    description: "Create, read, update, delete, export, import, clone, share dashboards"
    # Too many operations → ambiguous
```

**Pattern:**
```yaml
tools:
  - name: list_dashboards
    description: "List all dashboards in the workspace"

  - name: get_dashboard
    description: "Get a specific dashboard by ID"

  - name: create_dashboard
    description: "Create a new dashboard from spec"

  - name: export_dashboard
    description: "Export dashboard to YAML for version control"
```

**Our Implementation:**

| Tool | Single Responsibility |
|------|----------------------|
| `hybrid compile` | Render Jinja2 → YAML bundles |
| `hybrid validate` | Check bundle schema |
| `hybrid plan` | Show what would change |
| `hybrid apply` | Execute changes |
| `hybrid drift-plan` | Compare runtime vs repo |
| `hybrid export` | Dump runtime state |
| `hybrid translate` | Convert export → templates |

### 2. Examples (Curate, Don't Stuff)

> "Teams often stuff a laundry list of edge cases into a prompt. We do not recommend this."

**Anti-pattern:**
```markdown
## Examples
- If user asks for sales, check if they mean gross or net
- If date format is ambiguous, assume US format
- If region is missing, default to "all"
- If the dashboard has filters, apply them first
- ... (50 more edge cases)
```

**Pattern:**
```markdown
## Canonical Examples

### Example 1: Simple Query
Input: "Show me revenue by region"
Action: Query dataset with GROUP BY region

### Example 2: Time-Filtered Query
Input: "Revenue last month by region"
Action: Add WHERE date >= date_trunc('month', now() - interval '1 month')

### Example 3: Dashboard Creation
Input: "Create a sales overview dashboard"
Action: Generate spec with KPI row, trend line, breakdown table
```

### 3. Context Scoping (Informative Yet Tight)

**What to include:**
- Current environment (dev/staging/prod)
- Relevant schema subset (not full DB)
- Recent changes (last 5 commits, not full history)
- Active filters/state

**What to exclude:**
- Unrelated tables
- Historical logs
- Full file contents when summaries suffice
- Redundant information

**Implementation:**
```python
def build_context(env: str, task: str) -> dict:
    """Build minimal effective context for task."""
    return {
        # Environment scope
        "env": env,
        "superset_url": get_url(env),

        # Relevant state only
        "current_dashboards": list_dashboards(limit=10),
        "recent_changes": git_log(limit=5),

        # Schema subset
        "datasets": get_datasets_for_task(task),

        # NOT included: full DB schema, all history, unrelated assets
    }
```

### 4. Message History (Prune Aggressively)

For long-running agents, the context window fills up. Strategy:

```python
def prune_history(messages: list, max_tokens: int = 50000) -> list:
    """Keep recent + important messages within token budget."""

    # Always keep
    system = [m for m in messages if m["role"] == "system"]

    # Summarize old tool results
    summarized = summarize_old_tool_calls(messages)

    # Keep recent exchanges
    recent = messages[-10:]

    return system + summarized + recent
```

### 5. Dynamic Context Loading

Load context based on current task, not statically:

```python
CONTEXT_LOADERS = {
    "create_dashboard": lambda: {
        "datasets": list_datasets(),
        "chart_types": get_viz_catalog(),
        "templates": list_templates(),
    },
    "debug_query": lambda: {
        "schema": get_relevant_schema(),
        "recent_errors": get_error_log(limit=5),
        "query_history": get_recent_queries(limit=3),
    },
    "drift_detection": lambda: {
        "repo_state": get_bundle_manifest(),
        "runtime_state": export_current_state(),
        "last_deploy": get_deployment_info(),
    },
}

def get_context_for_task(task: str) -> dict:
    loader = CONTEXT_LOADERS.get(task, lambda: {})
    return loader()
```

---

## Context Directory Structure

Align with [SIP-189](https://github.com/apache/superset/issues/SIP-189):

```
context/
├── architecture/           # System design docs
│   ├── overview.md
│   ├── data-flow.md
│   └── components.md
│
├── workflows/              # How-to guides
│   ├── create-dashboard.md
│   ├── deploy-changes.md
│   └── debug-issues.md
│
├── decisions/              # ADRs
│   ├── adr-001-echarts.md
│   ├── adr-002-gitops.md
│   └── adr-003-temporal.md
│
├── examples/               # Canonical examples
│   ├── simple-dashboard.yaml
│   ├── filtered-query.sql
│   └── multi-env-deploy.sh
│
└── schemas/                # JSON schemas
    ├── plan.schema.json
    ├── apply.schema.json
    └── drift.schema.json
```

---

## MCP Context Resources

Expose context via MCP resources for agent consumption:

```typescript
// MCP resource definitions
server.setRequestHandler("resources/list", async () => ({
  resources: [
    {
      uri: "context://architecture",
      name: "Architecture Overview",
      mimeType: "text/markdown"
    },
    {
      uri: "context://workflow/create-dashboard",
      name: "Dashboard Creation Workflow",
      mimeType: "text/markdown"
    },
    {
      uri: "context://examples/canonical",
      name: "Canonical Examples",
      mimeType: "application/json"
    },
    {
      uri: "context://schema/current",
      name: "Current DB Schema (relevant subset)",
      mimeType: "application/json"
    }
  ]
}));

// Dynamic context loading
server.setRequestHandler("resources/read", async (request) => {
  const uri = request.params.uri;

  if (uri === "context://schema/current") {
    // Load only relevant schema, not entire DB
    const task = getCurrentTask();
    const schema = getSchemaForTask(task);
    return { contents: [{ text: JSON.stringify(schema) }] };
  }

  // ... other handlers
});
```

---

## Metrics for Context Quality

Track these to optimize context:

| Metric | Target | Measurement |
|--------|--------|-------------|
| Context utilization | 60-80% | tokens_used / max_tokens |
| Relevance score | >0.8 | semantic_similarity(context, task) |
| Tool selection accuracy | >95% | correct_tool / total_calls |
| First-attempt success | >80% | success_first_try / total_tasks |

---

## Implementation Checklist

- [ ] Audit tool definitions for single responsibility
- [ ] Curate 3-5 canonical examples per task type
- [ ] Implement dynamic context loaders
- [ ] Add message history pruning
- [ ] Create context/ directory structure
- [ ] Expose context via MCP resources
- [ ] Add context utilization metrics

---

## Resources

- [Anthropic: Effective Context Engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Anthropic: Writing Tools for Agents](https://www.anthropic.com/engineering/writing-tools-for-agents)
- [Anthropic: Effective Harnesses for Long-Running Agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [Anthropic: Building Agents with Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)
