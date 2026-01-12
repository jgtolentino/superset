# Tableau Reverse Engineering Skills

## Overview

This skill set enables reverse-engineering Tableau dashboards into:
- Semantic model extraction
- Odoo 18 CE + OCA data model mappings
- Apache Superset dashboard templates
- Workflow automation specifications

## When to Use

- Converting Tableau Public dashboards to Superset
- Analyzing Tableau workbook (.twb/.twbx) semantic models
- Creating Odoo-compatible KPI definitions
- Building reusable BI workflow blueprints

## Skills Included

1. `fetch_tableau_gallery_index` - Scrape Tableau Public gallery
2. `download_tableau_workbook` - Download .twb/.twbx files
3. `parse_tableau_semantic_model` - Extract tables, measures, visuals
4. `map_tableau_to_odoo_models` - Map to Odoo 18 CE + OCA
5. `generate_superset_templates_from_semantics` - Create Superset configs
6. `generate_workflow_automation_template` - Create Odoo automation specs
7. `export_superset_bundle` - Package for Superset import

## Pipeline

```
Tableau Gallery URL
        │
        ▼
fetch_tableau_gallery_index
        │
        ▼
download_tableau_workbook
        │
        ▼
parse_tableau_semantic_model
        │
        ├──────────────────────┐
        ▼                      ▼
map_tableau_to_odoo    generate_superset_templates
        │                      │
        ▼                      ▼
workflow_automation    export_superset_bundle
```

## Usage

```bash
# Run full pipeline
python skills/tableau-reverse-engineer/pipeline.py \
  --gallery-url "https://public.tableau.com/app/discover/business-dashboards" \
  --output-dir ./output

# Process single workbook
python skills/tableau-reverse-engineer/parse_semantic.py \
  --workbook ./dashboard.twbx \
  --output ./semantic_model.json
```

## Required Environment Variables

```bash
# Optional: Tableau Public API (if available)
TABLEAU_PUBLIC_API_KEY=

# Odoo connection (for validation)
ODOO_URL=
ODOO_DB=
ODOO_USER=
ODOO_PASSWORD=

# Superset connection (for export)
SUPERSET_URL=
SUPERSET_API_TOKEN=
```
