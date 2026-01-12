#!/usr/bin/env python3
"""
Skill: generate_superset_templates_from_semantics
Intent: Generate Superset dataset and dashboard templates from semantic mapping

Creates Superset-compatible configurations for:
- Datasets (SQL queries, columns, metrics)
- Charts (visualizations)
- Dashboards (layouts, filters)
"""

import json
import re
from dataclasses import dataclass, field, asdict
from typing import Optional, Any
from datetime import datetime


@dataclass
class SupersetMetric:
    """Superset metric definition."""
    metric_name: str
    verbose_name: str
    expression: str
    metric_type: str = "count"
    description: str = ""
    d3format: Optional[str] = None
    warning_text: Optional[str] = None


@dataclass
class SupersetColumn:
    """Superset column definition."""
    column_name: str
    verbose_name: str
    type: str
    is_dttm: bool = False
    filterable: bool = True
    groupby: bool = True
    description: str = ""


@dataclass
class SupersetDataset:
    """Superset dataset definition."""
    table_name: str
    database_name: str
    schema: Optional[str]
    sql: Optional[str]
    columns: list[SupersetColumn] = field(default_factory=list)
    metrics: list[SupersetMetric] = field(default_factory=list)
    main_dttm_col: Optional[str] = None
    description: str = ""
    is_sqllab_view: bool = False


@dataclass
class SupersetChart:
    """Superset chart configuration."""
    slice_name: str
    viz_type: str
    datasource_name: str
    params: dict = field(default_factory=dict)
    description: str = ""


@dataclass
class SupersetFilter:
    """Superset native filter."""
    name: str
    filter_type: str
    targets: list[dict] = field(default_factory=list)
    default_value: Optional[Any] = None
    description: str = ""


@dataclass
class SupersetDashboard:
    """Superset dashboard definition."""
    dashboard_title: str
    slug: str
    charts: list[str] = field(default_factory=list)
    filters: list[SupersetFilter] = field(default_factory=list)
    position_json: dict = field(default_factory=dict)
    css: str = ""
    json_metadata: dict = field(default_factory=dict)


# Tableau to Superset viz type mapping
VIZ_TYPE_MAP = {
    "bar_chart": "echarts_timeseries_bar",
    "line_chart": "echarts_timeseries_line",
    "area_chart": "echarts_area",
    "pie_chart": "pie",
    "scatter": "echarts_timeseries_scatter",
    "heatmap": "heatmap",
    "table": "table",
    "map": "deck_geojson",
    "gantt": "echarts_timeseries_bar",
    "treemap": "treemap_v2",
    "auto": "echarts_timeseries_bar",
    "unknown": "table",
}


class SupersetTemplateGenerator:
    """Generates Superset templates from Odoo mapping and semantic model."""

    def __init__(self):
        self.generated_at = datetime.utcnow().isoformat()

    def generate_templates(
        self,
        odoo_mapping: dict,
        semantic_model: dict,
        dashboard_title: Optional[str] = None,
        database_name: str = "odoo_warehouse"
    ) -> dict:
        """
        Generate Superset templates from Odoo mapping and semantic model.

        Args:
            odoo_mapping: Odoo model mapping from map_tableau_to_odoo_models
            semantic_model: Original Tableau semantic model
            dashboard_title: Override dashboard title
            database_name: Superset database connection name

        Returns:
            Dict with datasets, charts, dashboard, filters
        """
        # Generate datasets
        datasets = self._generate_datasets(
            odoo_mapping,
            semantic_model,
            database_name
        )

        # Generate charts
        charts = self._generate_charts(
            semantic_model.get("visuals", []),
            datasets,
            odoo_mapping
        )

        # Generate filters
        filters = self._generate_filters(
            semantic_model.get("filters", []),
            datasets
        )

        # Generate dashboard
        title = dashboard_title or self._infer_dashboard_title(semantic_model)
        dashboard = self._generate_dashboard(
            title,
            charts,
            filters,
            semantic_model.get("dashboards", [])
        )

        return {
            "superset_template": {
                "datasets": [asdict(d) for d in datasets],
                "charts": [asdict(c) for c in charts],
                "dashboard": asdict(dashboard),
                "filters": [asdict(f) for f in filters],
                "generated_at": self.generated_at,
                "database_name": database_name,
            }
        }

    def _generate_datasets(
        self,
        odoo_mapping: dict,
        semantic_model: dict,
        database_name: str
    ) -> list[SupersetDataset]:
        """Generate Superset dataset definitions."""
        datasets = []

        # Use suggested views from Odoo mapping
        for view in odoo_mapping.get("suggested_views", []):
            dataset = SupersetDataset(
                table_name=view.get("view_name"),
                database_name=database_name,
                schema="public",
                sql=None,  # Use view directly
                description=view.get("description", ""),
            )

            # Add columns from the base model
            base_model = view.get("base_model", "")
            for entity in odoo_mapping.get("entity_mappings", []):
                if entity.get("odoo_model") == base_model:
                    for field_map in entity.get("field_mappings", []):
                        col = SupersetColumn(
                            column_name=field_map.get("odoo_field"),
                            verbose_name=field_map.get("tableau_column", "").replace("_", " ").title(),
                            type=self._map_datatype(field_map.get("datatype", "string")),
                            is_dttm=field_map.get("datatype") in ["date", "datetime"],
                            groupby=field_map.get("role") == "dimension",
                        )
                        dataset.columns.append(col)

            # Add metrics from KPI expressions
            for kpi in odoo_mapping.get("kpi_expressions", []):
                if kpi.get("odoo_model") == base_model:
                    metric = SupersetMetric(
                        metric_name=self._to_snake_case(kpi.get("name", "")),
                        verbose_name=kpi.get("name", ""),
                        expression=kpi.get("sql_expression", ""),
                        metric_type=self._infer_metric_type(kpi.get("sql_expression", "")),
                        description=kpi.get("description", ""),
                    )
                    dataset.metrics.append(metric)

            # Set main datetime column
            for col in dataset.columns:
                if col.is_dttm:
                    dataset.main_dttm_col = col.column_name
                    break

            datasets.append(dataset)

        # If no views, create dataset from first entity mapping
        if not datasets and odoo_mapping.get("entity_mappings"):
            mapping = odoo_mapping["entity_mappings"][0]
            odoo_model = mapping.get("odoo_model", "")
            table_name = odoo_model.replace(".", "_")

            dataset = SupersetDataset(
                table_name=table_name,
                database_name=database_name,
                schema="public",
                description=f"Auto-generated from {mapping.get('tableau_entity')}",
            )

            for field_map in mapping.get("field_mappings", []):
                col = SupersetColumn(
                    column_name=field_map.get("odoo_field"),
                    verbose_name=field_map.get("tableau_column", "").replace("_", " ").title(),
                    type=self._map_datatype(field_map.get("datatype", "string")),
                )
                dataset.columns.append(col)

            for kpi in odoo_mapping.get("kpi_expressions", []):
                metric = SupersetMetric(
                    metric_name=self._to_snake_case(kpi.get("name", "")),
                    verbose_name=kpi.get("name", ""),
                    expression=kpi.get("sql_expression", ""),
                )
                dataset.metrics.append(metric)

            datasets.append(dataset)

        return datasets

    def _generate_charts(
        self,
        visuals: list[dict],
        datasets: list[SupersetDataset],
        odoo_mapping: dict
    ) -> list[SupersetChart]:
        """Generate Superset chart configurations."""
        charts = []

        # Get default dataset
        default_dataset = datasets[0].table_name if datasets else "default"

        for visual in visuals:
            # Map visual type
            tableau_type = visual.get("visual_type", "unknown")
            superset_type = VIZ_TYPE_MAP.get(tableau_type, "table")

            # Build chart params
            params = self._build_chart_params(
                visual,
                superset_type,
                datasets,
                odoo_mapping
            )

            chart = SupersetChart(
                slice_name=visual.get("title") or visual.get("name", "Chart"),
                viz_type=superset_type,
                datasource_name=default_dataset,
                params=params,
                description=f"Converted from Tableau visual: {visual.get('name')}",
            )

            charts.append(chart)

        return charts

    def _build_chart_params(
        self,
        visual: dict,
        viz_type: str,
        datasets: list[SupersetDataset],
        odoo_mapping: dict
    ) -> dict:
        """Build chart parameters based on visual type."""
        params = {
            "datasource": f"{datasets[0].table_name}__table" if datasets else None,
            "viz_type": viz_type,
        }

        # Map columns to Odoo fields
        field_mappings = {}
        for entity in odoo_mapping.get("entity_mappings", []):
            for fm in entity.get("field_mappings", []):
                field_mappings[fm.get("tableau_column", "").lower()] = fm.get("odoo_field")

        def map_field(tableau_field: str) -> str:
            return field_mappings.get(tableau_field.lower(), tableau_field)

        # Set groupby (dimensions)
        groupby = []
        for col in visual.get("rows_shelf", []) + visual.get("columns_used", []):
            mapped = map_field(col)
            if mapped and mapped not in groupby:
                groupby.append(mapped)
        params["groupby"] = groupby[:3]  # Limit to 3 dimensions

        # Set metrics
        metrics = []
        for measure in visual.get("measures_used", []):
            metric_name = self._to_snake_case(measure)
            metrics.append(metric_name)
        params["metrics"] = metrics if metrics else ["count"]

        # Type-specific params
        if viz_type in ["echarts_timeseries_bar", "echarts_timeseries_line"]:
            params["x_axis"] = groupby[0] if groupby else "date"
            params["time_grain_sqla"] = "P1M"

        elif viz_type == "pie":
            params["groupby"] = groupby[:1]
            params["metric"] = metrics[0] if metrics else "count"

        elif viz_type == "table":
            params["all_columns"] = groupby + metrics
            params["percent_metrics"] = []

        elif viz_type == "heatmap":
            params["all_columns_x"] = groupby[:1]
            params["all_columns_y"] = groupby[1:2] if len(groupby) > 1 else groupby[:1]
            params["metric"] = metrics[0] if metrics else "count"

        return params

    def _generate_filters(
        self,
        tableau_filters: list[dict],
        datasets: list[SupersetDataset]
    ) -> list[SupersetFilter]:
        """Generate Superset native filters."""
        filters = []
        default_dataset = datasets[0].table_name if datasets else "default"

        for tf in tableau_filters:
            filter_type = "filter_select"
            if tf.get("filter_type") == "range":
                filter_type = "filter_range"
            elif tf.get("filter_type") == "relative_date":
                filter_type = "filter_time"

            superset_filter = SupersetFilter(
                name=tf.get("name", tf.get("column", "Filter")),
                filter_type=filter_type,
                targets=[{
                    "datasetId": default_dataset,
                    "column": {"name": tf.get("column", "")},
                }],
                default_value=tf.get("values", []) if tf.get("values") else None,
            )

            filters.append(superset_filter)

        # Add default time filter if not present
        has_time_filter = any(f.filter_type == "filter_time" for f in filters)
        if not has_time_filter and datasets:
            for ds in datasets:
                if ds.main_dttm_col:
                    filters.insert(0, SupersetFilter(
                        name="Time Range",
                        filter_type="filter_time",
                        targets=[{
                            "datasetId": ds.table_name,
                            "column": {"name": ds.main_dttm_col},
                        }],
                        description="Auto-generated time filter",
                    ))
                    break

        return filters

    def _generate_dashboard(
        self,
        title: str,
        charts: list[SupersetChart],
        filters: list[SupersetFilter],
        tableau_dashboards: list[dict]
    ) -> SupersetDashboard:
        """Generate Superset dashboard configuration."""
        slug = self._to_snake_case(title)

        # Build position JSON (grid layout)
        position_json = self._build_position_json(charts)

        # Build metadata
        json_metadata = {
            "timed_refresh_immune_slices": [],
            "expanded_slices": {},
            "refresh_frequency": 0,
            "default_filters": "{}",
            "color_scheme": "supersetColors",
            "label_colors": {},
            "shared_label_colors": {},
            "color_scheme_domain": [],
            "cross_filters_enabled": True,
            "native_filter_configuration": [
                {
                    "id": f"filter_{i}",
                    "name": f.name,
                    "filterType": f.filter_type,
                    "targets": f.targets,
                    "defaultDataMask": {"filterState": {"value": f.default_value}},
                    "scope": {"rootPath": ["ROOT_ID"], "excluded": []},
                }
                for i, f in enumerate(filters)
            ],
        }

        # Get dimensions from Tableau dashboard
        width = 1200
        height = 800
        if tableau_dashboards:
            width = tableau_dashboards[0].get("width") or 1200
            height = tableau_dashboards[0].get("height") or 800

        dashboard = SupersetDashboard(
            dashboard_title=title,
            slug=slug,
            charts=[c.slice_name for c in charts],
            filters=filters,
            position_json=position_json,
            json_metadata=json_metadata,
        )

        return dashboard

    def _build_position_json(self, charts: list[SupersetChart]) -> dict:
        """Build dashboard position JSON for grid layout."""
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
                "meta": {"text": "Dashboard"},
            },
        }

        # Place charts in a grid (2 columns)
        row_height = 50  # Superset grid units
        col_width = 6   # Half of 12-column grid

        for i, chart in enumerate(charts):
            row = i // 2
            col = i % 2

            chart_id = f"CHART-{i}"
            row_id = f"ROW-{row}"

            # Create row if needed
            if row_id not in position:
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
                "parents": ["ROOT_ID", "GRID_ID", row_id],
                "meta": {
                    "chartId": i + 1,
                    "width": col_width,
                    "height": row_height,
                    "sliceName": chart.slice_name,
                },
            }
            position[row_id]["children"].append(chart_id)

        return position

    def _infer_dashboard_title(self, semantic_model: dict) -> str:
        """Infer dashboard title from semantic model."""
        dashboards = semantic_model.get("dashboards", [])
        if dashboards:
            return dashboards[0].get("title") or dashboards[0].get("name", "Dashboard")

        visuals = semantic_model.get("visuals", [])
        if visuals:
            return f"{visuals[0].get('name', 'Tableau')} Dashboard"

        return "Converted Dashboard"

    def _map_datatype(self, tableau_type: str) -> str:
        """Map Tableau datatype to Superset column type."""
        type_map = {
            "string": "STRING",
            "integer": "INT",
            "float": "FLOAT",
            "date": "DATE",
            "datetime": "DATETIME",
            "boolean": "BOOLEAN",
        }
        return type_map.get(tableau_type, "STRING")

    def _infer_metric_type(self, expression: str) -> str:
        """Infer metric type from SQL expression."""
        expr_lower = expression.lower()
        if "count" in expr_lower:
            return "count"
        elif "sum" in expr_lower:
            return "sum"
        elif "avg" in expr_lower:
            return "avg"
        elif "max" in expr_lower:
            return "max"
        elif "min" in expr_lower:
            return "min"
        return "expression"

    def _to_snake_case(self, text: str) -> str:
        """Convert text to snake_case."""
        # Remove special characters
        text = re.sub(r'[^\w\s]', '', text)
        # Replace spaces with underscores
        text = re.sub(r'\s+', '_', text)
        # Convert to lowercase
        return text.lower()


# =============================================================================
# SKILL HANDLER
# =============================================================================
async def handle(inputs: dict) -> dict:
    """
    Skill handler for generate_superset_templates_from_semantics.

    Args:
        inputs: Dict with odoo_mapping, semantic_model, dashboard_title, database_name

    Returns:
        Dict with superset_template
    """
    odoo_mapping = inputs.get("odoo_mapping")
    if not odoo_mapping:
        raise ValueError("odoo_mapping is required")

    semantic_model = inputs.get("semantic_model")
    if not semantic_model:
        raise ValueError("semantic_model is required")

    dashboard_title = inputs.get("dashboard_title")
    database_name = inputs.get("database_name", "odoo_warehouse")

    generator = SupersetTemplateGenerator()
    result = generator.generate_templates(
        odoo_mapping=odoo_mapping,
        semantic_model=semantic_model,
        dashboard_title=dashboard_title,
        database_name=database_name
    )

    return result


# =============================================================================
# VALIDATION EXAMPLE
# =============================================================================
VALIDATION_EXAMPLE = {
    "input": {
        "odoo_mapping": {
            "entity_mappings": [
                {
                    "tableau_entity": "orders",
                    "odoo_model": "sale.order",
                    "field_mappings": [
                        {"tableau_column": "order_id", "odoo_field": "id", "datatype": "integer"},
                        {"tableau_column": "amount", "odoo_field": "amount_total", "datatype": "float"}
                    ]
                }
            ],
            "kpi_expressions": [
                {"name": "Total Sales", "sql_expression": "SUM(amount_total)", "odoo_model": "sale.order"}
            ],
            "suggested_views": [
                {"view_name": "bi_sale_order_summary", "base_model": "sale.order", "sql": "..."}
            ]
        },
        "semantic_model": {
            "visuals": [
                {"name": "Sales Chart", "visual_type": "bar_chart", "measures_used": ["Total Sales"]}
            ],
            "filters": [
                {"name": "Date Filter", "column": "date_order", "filter_type": "range"}
            ],
            "dashboards": [
                {"name": "Sales Dashboard", "title": "Sales Performance"}
            ]
        },
        "database_name": "odoo_warehouse"
    },
    "output": {
        "superset_template": {
            "datasets": [
                {
                    "table_name": "bi_sale_order_summary",
                    "database_name": "odoo_warehouse",
                    "schema": "public",
                    "columns": [
                        {"column_name": "id", "verbose_name": "Order Id", "type": "INT"},
                        {"column_name": "amount_total", "verbose_name": "Amount", "type": "FLOAT"}
                    ],
                    "metrics": [
                        {"metric_name": "total_sales", "verbose_name": "Total Sales", "expression": "SUM(amount_total)"}
                    ]
                }
            ],
            "charts": [
                {
                    "slice_name": "Sales Chart",
                    "viz_type": "echarts_timeseries_bar",
                    "datasource_name": "bi_sale_order_summary",
                    "params": {"metrics": ["total_sales"], "groupby": []}
                }
            ],
            "dashboard": {
                "dashboard_title": "Sales Performance",
                "slug": "sales_performance",
                "charts": ["Sales Chart"]
            },
            "filters": [
                {"name": "Date Filter", "filter_type": "filter_range"}
            ]
        }
    }
}


if __name__ == "__main__":
    print(json.dumps(VALIDATION_EXAMPLE, indent=2))
