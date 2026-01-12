#!/usr/bin/env python3
"""
Export Superset Bundle Skill Handler

Packages generated Superset templates into importable ZIP bundles
compatible with Superset's native import functionality.

Bundle Structure:
  superset_export_YYYYMMDD_HHMMSS/
  ├── metadata.yaml           # Bundle metadata and manifest
  ├── databases/
  │   └── database.yaml       # Database connection config
  ├── datasets/
  │   ├── dataset_1.yaml      # Dataset definitions
  │   └── dataset_2.yaml
  ├── charts/
  │   ├── chart_1.yaml        # Chart configurations
  │   └── chart_2.yaml
  ├── dashboards/
  │   └── dashboard.yaml      # Dashboard layout and filters
  └── assets/                 # Optional static assets
      └── thumbnails/

Usage:
    python export_bundle.py <superset_templates_json> [--output-dir ./bundles]

    # Or import as module
    from export_bundle import export_superset_bundle

    result = export_superset_bundle(
        superset_templates=templates,
        output_dir="./bundles",
        bundle_name="sales_analytics"
    )
"""

import json
import os
import sys
import zipfile
import yaml
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field, asdict
import hashlib
import uuid


# ============================================================================
# Data Classes for Bundle Components
# ============================================================================

@dataclass
class BundleMetadata:
    """Bundle metadata and manifest."""
    version: str = "1.0.0"
    type: str = "superset_bundle"
    timestamp: str = ""
    source: str = "tableau-reverse-engineer"
    bundle_id: str = ""
    name: str = ""
    description: str = ""

    # Contents summary
    database_count: int = 0
    dataset_count: int = 0
    chart_count: int = 0
    dashboard_count: int = 0

    # Source tracking
    source_workbook: str = ""
    source_type: str = "tableau"

    # Compatibility
    superset_version_min: str = "3.0.0"
    superset_version_max: str = "4.x"

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat() + "Z"
        if not self.bundle_id:
            self.bundle_id = str(uuid.uuid4())


@dataclass
class DatabaseExport:
    """Database connection export format."""
    database_name: str
    sqlalchemy_uri: str = ""
    expose_in_sqllab: bool = True
    allow_ctas: bool = False
    allow_cvas: bool = False
    allow_dml: bool = False
    allow_run_async: bool = True
    cache_timeout: Optional[int] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    # Placeholder for actual URI
    uri_placeholder: str = "${SUPERSET_DATABASE_URI}"

    def to_yaml_dict(self) -> Dict[str, Any]:
        """Convert to YAML-exportable dict with placeholders."""
        return {
            "database_name": self.database_name,
            "sqlalchemy_uri": self.uri_placeholder,
            "expose_in_sqllab": self.expose_in_sqllab,
            "allow_ctas": self.allow_ctas,
            "allow_cvas": self.allow_cvas,
            "allow_dml": self.allow_dml,
            "allow_run_async": self.allow_run_async,
            "cache_timeout": self.cache_timeout,
            "extra": json.dumps(self.extra) if self.extra else "{}",
            "version": "1.0.0",
            "uuid": str(uuid.uuid4()),
        }


@dataclass
class DatasetExport:
    """Dataset export format compatible with Superset import."""
    table_name: str
    schema: str = ""
    database_uuid: str = ""
    sql: Optional[str] = None
    description: str = ""

    # Columns
    columns: List[Dict[str, Any]] = field(default_factory=list)

    # Metrics
    metrics: List[Dict[str, Any]] = field(default_factory=list)

    # Configuration
    main_dttm_col: Optional[str] = None
    offset: int = 0
    default_endpoint: Optional[str] = None
    filter_select_enabled: bool = True
    fetch_values_predicate: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)

    # UUID for import matching
    uuid: str = ""

    def __post_init__(self):
        if not self.uuid:
            self.uuid = str(uuid.uuid4())

    def to_yaml_dict(self) -> Dict[str, Any]:
        """Convert to YAML-exportable dict."""
        result = {
            "table_name": self.table_name,
            "schema": self.schema,
            "sql": self.sql,
            "description": self.description,
            "main_dttm_col": self.main_dttm_col,
            "offset": self.offset,
            "filter_select_enabled": self.filter_select_enabled,
            "extra": json.dumps(self.extra) if self.extra else None,
            "uuid": self.uuid,
            "version": "1.0.0",
            "database_uuid": self.database_uuid,
        }

        # Add columns with proper format
        if self.columns:
            result["columns"] = [
                {
                    "column_name": col.get("column_name", col.get("name", "")),
                    "type": col.get("type", "VARCHAR"),
                    "groupby": col.get("groupby", True),
                    "filterable": col.get("filterable", True),
                    "expression": col.get("expression"),
                    "description": col.get("description", ""),
                    "verbose_name": col.get("verbose_name", col.get("column_name", "")),
                    "is_dttm": col.get("is_dttm", False),
                }
                for col in self.columns
            ]

        # Add metrics with proper format
        if self.metrics:
            result["metrics"] = [
                {
                    "metric_name": m.get("metric_name", m.get("name", "")),
                    "verbose_name": m.get("verbose_name", m.get("metric_name", "")),
                    "expression": m.get("expression", m.get("sql", "")),
                    "metric_type": m.get("metric_type", ""),
                    "description": m.get("description", ""),
                    "d3format": m.get("d3format"),
                    "warning_text": m.get("warning_text"),
                }
                for m in self.metrics
            ]

        return result


@dataclass
class ChartExport:
    """Chart export format compatible with Superset import."""
    slice_name: str
    viz_type: str
    description: str = ""

    # Data source
    datasource_id: Optional[int] = None
    datasource_type: str = "table"
    datasource_uuid: str = ""

    # Query configuration
    params: Dict[str, Any] = field(default_factory=dict)
    query_context: Optional[str] = None

    # Display
    cache_timeout: Optional[int] = None

    # UUID
    uuid: str = ""

    def __post_init__(self):
        if not self.uuid:
            self.uuid = str(uuid.uuid4())

    def to_yaml_dict(self) -> Dict[str, Any]:
        """Convert to YAML-exportable dict."""
        return {
            "slice_name": self.slice_name,
            "viz_type": self.viz_type,
            "description": self.description,
            "datasource_type": self.datasource_type,
            "datasource_uuid": self.datasource_uuid,
            "params": json.dumps(self.params),
            "query_context": self.query_context,
            "cache_timeout": self.cache_timeout,
            "uuid": self.uuid,
            "version": "1.0.0",
        }


@dataclass
class DashboardExport:
    """Dashboard export format compatible with Superset import."""
    dashboard_title: str
    slug: str = ""
    description: str = ""

    # Layout
    position_json: str = "{}"
    json_metadata: str = "{}"

    # Charts included
    chart_uuids: List[str] = field(default_factory=list)

    # Filters
    native_filters: List[Dict[str, Any]] = field(default_factory=list)

    # Configuration
    css: str = ""
    published: bool = False

    # UUID
    uuid: str = ""

    def __post_init__(self):
        if not self.uuid:
            self.uuid = str(uuid.uuid4())
        if not self.slug:
            self.slug = self.dashboard_title.lower().replace(" ", "_").replace("-", "_")

    def to_yaml_dict(self) -> Dict[str, Any]:
        """Convert to YAML-exportable dict."""
        metadata = json.loads(self.json_metadata) if isinstance(self.json_metadata, str) else self.json_metadata

        # Add native filters to metadata
        if self.native_filters:
            metadata["native_filter_configuration"] = self.native_filters

        return {
            "dashboard_title": self.dashboard_title,
            "slug": self.slug,
            "description": self.description,
            "position": json.loads(self.position_json) if isinstance(self.position_json, str) else self.position_json,
            "metadata": metadata,
            "css": self.css,
            "published": self.published,
            "uuid": self.uuid,
            "version": "1.0.0",
        }


# ============================================================================
# Bundle Builder
# ============================================================================

class SupersetBundleBuilder:
    """
    Builds Superset-compatible import bundles from generated templates.
    """

    def __init__(self, bundle_name: str, output_dir: str = "./bundles"):
        self.bundle_name = bundle_name
        self.output_dir = Path(output_dir)
        self.timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        # Components
        self.databases: List[DatabaseExport] = []
        self.datasets: List[DatasetExport] = []
        self.charts: List[ChartExport] = []
        self.dashboards: List[DashboardExport] = []

        # UUID mappings for cross-references
        self.database_uuid_map: Dict[str, str] = {}  # name -> uuid
        self.dataset_uuid_map: Dict[str, str] = {}   # name -> uuid
        self.chart_uuid_map: Dict[str, str] = {}     # name -> uuid

        # Metadata
        self.metadata = BundleMetadata(name=bundle_name)

    def add_database(self, name: str, **kwargs) -> str:
        """Add database connection and return its UUID."""
        db = DatabaseExport(database_name=name, **kwargs)
        db_uuid = str(uuid.uuid4())
        self.database_uuid_map[name] = db_uuid
        self.databases.append(db)
        return db_uuid

    def add_dataset(self, dataset_dict: Dict[str, Any]) -> str:
        """Add dataset from template dict and return its UUID."""
        ds = DatasetExport(
            table_name=dataset_dict.get("table_name", dataset_dict.get("name", "untitled")),
            schema=dataset_dict.get("schema", ""),
            sql=dataset_dict.get("sql"),
            description=dataset_dict.get("description", ""),
            columns=dataset_dict.get("columns", []),
            metrics=dataset_dict.get("metrics", []),
            main_dttm_col=dataset_dict.get("main_dttm_col"),
            extra=dataset_dict.get("extra", {}),
        )

        # Link to database if specified
        db_name = dataset_dict.get("database", "")
        if db_name and db_name in self.database_uuid_map:
            ds.database_uuid = self.database_uuid_map[db_name]

        self.dataset_uuid_map[ds.table_name] = ds.uuid
        self.datasets.append(ds)
        return ds.uuid

    def add_chart(self, chart_dict: Dict[str, Any]) -> str:
        """Add chart from template dict and return its UUID."""
        chart = ChartExport(
            slice_name=chart_dict.get("slice_name", chart_dict.get("name", "untitled")),
            viz_type=chart_dict.get("viz_type", "table"),
            description=chart_dict.get("description", ""),
            params=chart_dict.get("params", {}),
            cache_timeout=chart_dict.get("cache_timeout"),
        )

        # Link to dataset if specified
        ds_name = chart_dict.get("datasource", chart_dict.get("dataset", ""))
        if ds_name and ds_name in self.dataset_uuid_map:
            chart.datasource_uuid = self.dataset_uuid_map[ds_name]

        self.chart_uuid_map[chart.slice_name] = chart.uuid
        self.charts.append(chart)
        return chart.uuid

    def add_dashboard(self, dashboard_dict: Dict[str, Any]) -> str:
        """Add dashboard from template dict and return its UUID."""
        dash = DashboardExport(
            dashboard_title=dashboard_dict.get("dashboard_title", dashboard_dict.get("name", "untitled")),
            slug=dashboard_dict.get("slug", ""),
            description=dashboard_dict.get("description", ""),
            position_json=json.dumps(dashboard_dict.get("position", {})),
            json_metadata=json.dumps(dashboard_dict.get("metadata", {})),
            native_filters=dashboard_dict.get("filters", []),
            css=dashboard_dict.get("css", ""),
            published=dashboard_dict.get("published", False),
        )

        # Collect chart UUIDs
        chart_names = dashboard_dict.get("charts", [])
        for name in chart_names:
            if name in self.chart_uuid_map:
                dash.chart_uuids.append(self.chart_uuid_map[name])

        self.dashboards.append(dash)
        return dash.uuid

    def load_from_templates(self, templates: Dict[str, Any]) -> None:
        """
        Load all components from generated Superset templates.

        Expected templates structure:
        {
            "datasets": [...],
            "charts": [...],
            "dashboards": [...],
            "filters": [...],
            "source_info": {...}
        }
        """
        # Add default database
        db_name = templates.get("database_name", "odoo_bi_db")
        self.add_database(db_name)

        # Add datasets
        for ds in templates.get("datasets", []):
            ds["database"] = db_name
            self.add_dataset(ds)

        # Add charts
        for chart in templates.get("charts", []):
            self.add_chart(chart)

        # Add dashboards
        for dash in templates.get("dashboards", []):
            self.add_dashboard(dash)

        # Update metadata
        if "source_info" in templates:
            self.metadata.source_workbook = templates["source_info"].get("workbook", "")
            self.metadata.source_type = templates["source_info"].get("type", "tableau")

        self.metadata.description = templates.get("description", f"Converted from {self.metadata.source_workbook}")

    def _generate_position_json(self, charts: List[ChartExport]) -> Dict[str, Any]:
        """Generate dashboard position layout for charts."""
        position = {
            "DASHBOARD_VERSION_KEY": "v2",
            "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
            "GRID_ID": {
                "type": "GRID",
                "id": "GRID_ID",
                "children": [],
                "parents": ["ROOT_ID"],
            },
            "HEADER_ID": {
                "type": "HEADER",
                "id": "HEADER_ID",
                "meta": {"text": self.bundle_name},
            },
        }

        # Layout charts in a grid (2 columns)
        row_idx = 0
        col_idx = 0
        cols_per_row = 2
        chart_width = 6  # Out of 12 columns
        chart_height = 50  # In grid units

        for i, chart in enumerate(charts):
            row_id = f"ROW-{row_idx}"
            chart_id = f"CHART-{chart.uuid[:8]}"

            # Create row if needed
            if col_idx == 0:
                position[row_id] = {
                    "type": "ROW",
                    "id": row_id,
                    "children": [],
                    "parents": ["GRID_ID"],
                    "meta": {"background": "BACKGROUND_TRANSPARENT"},
                }
                position["GRID_ID"]["children"].append(row_id)

            # Add chart to row
            position[chart_id] = {
                "type": "CHART",
                "id": chart_id,
                "children": [],
                "parents": [row_id],
                "meta": {
                    "width": chart_width,
                    "height": chart_height,
                    "chartId": chart.uuid,
                    "uuid": chart.uuid,
                    "sliceName": chart.slice_name,
                },
            }
            position[row_id]["children"].append(chart_id)

            # Move to next position
            col_idx += 1
            if col_idx >= cols_per_row:
                col_idx = 0
                row_idx += 1

        return position

    def build(self) -> Path:
        """
        Build the complete bundle as a ZIP file.
        Returns the path to the created bundle.
        """
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Bundle directory name
        bundle_dir_name = f"superset_export_{self.bundle_name}_{self.timestamp}"
        bundle_path = self.output_dir / f"{bundle_dir_name}.zip"

        # Update metadata counts
        self.metadata.database_count = len(self.databases)
        self.metadata.dataset_count = len(self.datasets)
        self.metadata.chart_count = len(self.charts)
        self.metadata.dashboard_count = len(self.dashboards)

        with zipfile.ZipFile(bundle_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Write metadata
            metadata_yaml = yaml.dump(asdict(self.metadata), default_flow_style=False, sort_keys=False)
            zf.writestr(f"{bundle_dir_name}/metadata.yaml", metadata_yaml)

            # Write databases
            for i, db in enumerate(self.databases):
                db_yaml = yaml.dump(db.to_yaml_dict(), default_flow_style=False, sort_keys=False)
                zf.writestr(f"{bundle_dir_name}/databases/{db.database_name}.yaml", db_yaml)

            # Write datasets
            for ds in self.datasets:
                ds_yaml = yaml.dump(ds.to_yaml_dict(), default_flow_style=False, sort_keys=False)
                safe_name = ds.table_name.replace("/", "_").replace("\\", "_")
                zf.writestr(f"{bundle_dir_name}/datasets/{safe_name}.yaml", ds_yaml)

            # Write charts
            for chart in self.charts:
                chart_yaml = yaml.dump(chart.to_yaml_dict(), default_flow_style=False, sort_keys=False)
                safe_name = chart.slice_name.replace("/", "_").replace("\\", "_")
                zf.writestr(f"{bundle_dir_name}/charts/{safe_name}.yaml", chart_yaml)

            # Write dashboards with position layout
            for dash in self.dashboards:
                # Generate position if not set
                if dash.position_json == "{}" and dash.chart_uuids:
                    # Find charts for this dashboard
                    dash_charts = [c for c in self.charts if c.uuid in dash.chart_uuids]
                    dash.position_json = json.dumps(self._generate_position_json(dash_charts))

                dash_yaml = yaml.dump(dash.to_yaml_dict(), default_flow_style=False, sort_keys=False)
                safe_name = dash.slug or dash.dashboard_title.replace("/", "_").replace("\\", "_")
                zf.writestr(f"{bundle_dir_name}/dashboards/{safe_name}.yaml", dash_yaml)

            # Write import manifest (for Superset CLI import)
            manifest = {
                "databases": [f"databases/{db.database_name}.yaml" for db in self.databases],
                "datasets": [f"datasets/{ds.table_name.replace('/', '_')}.yaml" for ds in self.datasets],
                "charts": [f"charts/{c.slice_name.replace('/', '_')}.yaml" for c in self.charts],
                "dashboards": [f"dashboards/{(d.slug or d.dashboard_title).replace('/', '_')}.yaml" for d in self.dashboards],
            }
            manifest_yaml = yaml.dump(manifest, default_flow_style=False, sort_keys=False)
            zf.writestr(f"{bundle_dir_name}/manifest.yaml", manifest_yaml)

        return bundle_path

    def build_individual_assets(self) -> Dict[str, Path]:
        """
        Build individual asset files (not zipped) for selective import.
        Returns dict mapping asset type to file paths.
        """
        # Create asset directories
        asset_dir = self.output_dir / f"superset_assets_{self.bundle_name}_{self.timestamp}"
        (asset_dir / "databases").mkdir(parents=True, exist_ok=True)
        (asset_dir / "datasets").mkdir(parents=True, exist_ok=True)
        (asset_dir / "charts").mkdir(parents=True, exist_ok=True)
        (asset_dir / "dashboards").mkdir(parents=True, exist_ok=True)

        created_files = {
            "databases": [],
            "datasets": [],
            "charts": [],
            "dashboards": [],
        }

        # Write databases
        for db in self.databases:
            path = asset_dir / "databases" / f"{db.database_name}.yaml"
            with open(path, 'w') as f:
                yaml.dump(db.to_yaml_dict(), f, default_flow_style=False, sort_keys=False)
            created_files["databases"].append(path)

        # Write datasets
        for ds in self.datasets:
            safe_name = ds.table_name.replace("/", "_").replace("\\", "_")
            path = asset_dir / "datasets" / f"{safe_name}.yaml"
            with open(path, 'w') as f:
                yaml.dump(ds.to_yaml_dict(), f, default_flow_style=False, sort_keys=False)
            created_files["datasets"].append(path)

        # Write charts
        for chart in self.charts:
            safe_name = chart.slice_name.replace("/", "_").replace("\\", "_")
            path = asset_dir / "charts" / f"{safe_name}.yaml"
            with open(path, 'w') as f:
                yaml.dump(chart.to_yaml_dict(), f, default_flow_style=False, sort_keys=False)
            created_files["charts"].append(path)

        # Write dashboards
        for dash in self.dashboards:
            safe_name = dash.slug or dash.dashboard_title.replace("/", "_").replace("\\", "_")
            path = asset_dir / "dashboards" / f"{safe_name}.yaml"
            with open(path, 'w') as f:
                yaml.dump(dash.to_yaml_dict(), f, default_flow_style=False, sort_keys=False)
            created_files["dashboards"].append(path)

        return created_files


# ============================================================================
# Main Export Function
# ============================================================================

def export_superset_bundle(
    superset_templates: Dict[str, Any],
    output_dir: str = "./bundles",
    bundle_name: Optional[str] = None,
    format: str = "zip",  # "zip" or "individual"
) -> Dict[str, Any]:
    """
    Export Superset templates as importable bundle.

    Args:
        superset_templates: Generated templates from generate_superset.py
        output_dir: Directory for output bundles
        bundle_name: Optional bundle name (derived from source if not provided)
        format: Output format - "zip" for single archive, "individual" for separate files

    Returns:
        Export result with paths and metadata
    """
    # Derive bundle name
    if not bundle_name:
        source_info = superset_templates.get("source_info", {})
        bundle_name = source_info.get("workbook", "").replace(".twbx", "").replace(".twb", "")
        if not bundle_name:
            bundle_name = "superset_bundle"
        bundle_name = bundle_name.lower().replace(" ", "_").replace("-", "_")

    # Build bundle
    builder = SupersetBundleBuilder(bundle_name, output_dir)
    builder.load_from_templates(superset_templates)

    if format == "zip":
        bundle_path = builder.build()
        return {
            "status": "success",
            "format": "zip",
            "bundle_path": str(bundle_path),
            "bundle_name": bundle_name,
            "metadata": asdict(builder.metadata),
            "contents": {
                "databases": len(builder.databases),
                "datasets": len(builder.datasets),
                "charts": len(builder.charts),
                "dashboards": len(builder.dashboards),
            },
            "import_command": f"superset import-dashboards -p {bundle_path}",
        }
    else:
        asset_paths = builder.build_individual_assets()
        return {
            "status": "success",
            "format": "individual",
            "asset_paths": {k: [str(p) for p in v] for k, v in asset_paths.items()},
            "bundle_name": bundle_name,
            "metadata": asdict(builder.metadata),
            "contents": {
                "databases": len(builder.databases),
                "datasets": len(builder.datasets),
                "charts": len(builder.charts),
                "dashboards": len(builder.dashboards),
            },
        }


def generate_import_script(bundle_path: str, superset_url: str = "${BASE_URL}") -> str:
    """
    Generate a shell script to import the bundle into Superset.

    Args:
        bundle_path: Path to the bundle ZIP file
        superset_url: Superset instance URL (uses env var by default)

    Returns:
        Shell script content
    """
    script = f'''#!/bin/bash
# Superset Bundle Import Script
# Generated by tableau-reverse-engineer skill

set -euo pipefail

# Configuration
BUNDLE_PATH="{bundle_path}"
SUPERSET_URL="{superset_url}"

# Check required environment variables
if [ -z "${{SUPERSET_ADMIN_USER:-}}" ]; then
    echo "BLOCKED: missing env var SUPERSET_ADMIN_USER"
    exit 1
fi

if [ -z "${{SUPERSET_ADMIN_PASS:-}}" ]; then
    echo "BLOCKED: missing env var SUPERSET_ADMIN_PASS"
    exit 1
fi

# Get access token
echo "Authenticating with Superset..."
TOKEN=$(curl -s -X POST "$SUPERSET_URL/api/v1/security/login" \\
    -H "Content-Type: application/json" \\
    -d '{{"username":"'"$SUPERSET_ADMIN_USER"'","password":"'"$SUPERSET_ADMIN_PASS"'","provider":"db"}}' \\
    | jq -r '.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
    echo "ERROR: Authentication failed"
    exit 1
fi

echo "Authenticated successfully"

# Import bundle
echo "Importing bundle: $BUNDLE_PATH"
RESPONSE=$(curl -s -X POST "$SUPERSET_URL/api/v1/dashboard/import/" \\
    -H "Authorization: Bearer $TOKEN" \\
    -H "Content-Type: multipart/form-data" \\
    -F "formData=@$BUNDLE_PATH" \\
    -F "overwrite=true")

# Check result
if echo "$RESPONSE" | jq -e '.message' > /dev/null 2>&1; then
    MESSAGE=$(echo "$RESPONSE" | jq -r '.message')
    if [ "$MESSAGE" != "OK" ]; then
        echo "ERROR: Import failed - $MESSAGE"
        exit 1
    fi
fi

echo "Bundle imported successfully!"
echo "Response: $RESPONSE"
'''
    return script


# ============================================================================
# CLI Entry Point
# ============================================================================

def main():
    """CLI entry point for bundle export."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Export Superset templates as importable bundle"
    )
    parser.add_argument(
        "templates_json",
        help="Path to JSON file with Superset templates"
    )
    parser.add_argument(
        "--output-dir", "-o",
        default="./bundles",
        help="Output directory for bundles (default: ./bundles)"
    )
    parser.add_argument(
        "--name", "-n",
        help="Bundle name (derived from source if not provided)"
    )
    parser.add_argument(
        "--format", "-f",
        choices=["zip", "individual"],
        default="zip",
        help="Output format (default: zip)"
    )
    parser.add_argument(
        "--generate-import-script", "-s",
        action="store_true",
        help="Generate import shell script"
    )
    parser.add_argument(
        "--superset-url",
        default="${BASE_URL}",
        help="Superset URL for import script"
    )

    args = parser.parse_args()

    # Load templates
    templates_path = Path(args.templates_json)
    if not templates_path.exists():
        print(f"ERROR: Templates file not found: {templates_path}")
        sys.exit(1)

    with open(templates_path) as f:
        templates = json.load(f)

    # Export bundle
    result = export_superset_bundle(
        superset_templates=templates,
        output_dir=args.output_dir,
        bundle_name=args.name,
        format=args.format,
    )

    # Print result
    print(json.dumps(result, indent=2))

    # Generate import script if requested
    if args.generate_import_script and args.format == "zip":
        script_path = Path(args.output_dir) / f"import_{result['bundle_name']}.sh"
        script_content = generate_import_script(
            result["bundle_path"],
            args.superset_url
        )
        with open(script_path, 'w') as f:
            f.write(script_content)
        os.chmod(script_path, 0o755)
        print(f"\nImport script generated: {script_path}")


if __name__ == "__main__":
    main()
