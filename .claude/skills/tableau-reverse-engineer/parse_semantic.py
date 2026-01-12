#!/usr/bin/env python3
"""
Skill: parse_tableau_semantic_model
Intent: Extract semantic model from Tableau workbook (tables, measures, visuals)

Parses .twb (XML) and .twbx (ZIP containing XML) files to extract:
- Data sources and connections
- Tables, columns, and data types
- Relationships between tables
- Calculated fields and measures
- Worksheets and visual configurations
- Filters and parameters
"""

import json
import os
import re
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, Any


@dataclass
class Column:
    """Represents a table column."""
    name: str
    datatype: str
    role: str  # dimension, measure
    caption: Optional[str] = None
    calculation: Optional[str] = None
    aggregation: Optional[str] = None
    semantic_role: Optional[str] = None


@dataclass
class Table:
    """Represents a data table."""
    name: str
    columns: list[Column] = field(default_factory=list)
    connection: Optional[str] = None
    schema: Optional[str] = None
    sql_query: Optional[str] = None


@dataclass
class Relationship:
    """Represents a table relationship."""
    left_table: str
    right_table: str
    left_column: str
    right_column: str
    relationship_type: str  # inner, left, right, full


@dataclass
class Measure:
    """Represents a calculated measure."""
    name: str
    caption: str
    formula: str
    datatype: str
    aggregation: Optional[str] = None
    description: Optional[str] = None


@dataclass
class Parameter:
    """Represents a dashboard parameter."""
    name: str
    caption: str
    datatype: str
    current_value: Any
    allowable_values: Optional[list] = None


@dataclass
class Filter:
    """Represents a filter."""
    name: str
    column: str
    filter_type: str  # categorical, range, relative_date
    values: Optional[list] = None
    range_min: Optional[Any] = None
    range_max: Optional[Any] = None
    scope: str = "global"  # global, worksheet


@dataclass
class Visual:
    """Represents a worksheet/visual."""
    name: str
    title: Optional[str]
    visual_type: str
    columns_used: list[str] = field(default_factory=list)
    measures_used: list[str] = field(default_factory=list)
    filters: list[str] = field(default_factory=list)
    mark_type: Optional[str] = None
    rows_shelf: list[str] = field(default_factory=list)
    cols_shelf: list[str] = field(default_factory=list)
    color_shelf: list[str] = field(default_factory=list)
    size_shelf: list[str] = field(default_factory=list)


@dataclass
class Dashboard:
    """Represents a dashboard layout."""
    name: str
    title: Optional[str]
    worksheets: list[str] = field(default_factory=list)
    width: Optional[int] = None
    height: Optional[int] = None
    device_layouts: list[str] = field(default_factory=list)


@dataclass
class SemanticModel:
    """Complete semantic model extracted from workbook."""
    datasources: list[dict] = field(default_factory=list)
    tables: list[Table] = field(default_factory=list)
    relationships: list[Relationship] = field(default_factory=list)
    measures: list[Measure] = field(default_factory=list)
    parameters: list[Parameter] = field(default_factory=list)
    filters: list[Filter] = field(default_factory=list)
    visuals: list[Visual] = field(default_factory=list)
    dashboards: list[Dashboard] = field(default_factory=list)


class TableauWorkbookParser:
    """Parses Tableau workbooks to extract semantic model."""

    # Tableau data type mappings
    DATATYPE_MAP = {
        "string": "string",
        "integer": "integer",
        "real": "float",
        "date": "date",
        "datetime": "datetime",
        "boolean": "boolean",
        "spatial": "geometry",
    }

    # Tableau aggregation mappings
    AGGREGATION_MAP = {
        "Sum": "SUM",
        "Avg": "AVG",
        "Min": "MIN",
        "Max": "MAX",
        "Count": "COUNT",
        "CountD": "COUNT_DISTINCT",
        "Median": "MEDIAN",
        "Attr": "ATTR",
        "None": None,
    }

    def __init__(self):
        self.namespaces = {
            "user": "http://www.tableausoftware.com/xml/user"
        }

    def parse_workbook(
        self,
        workbook_path: str,
        include_raw_xml: bool = False
    ) -> dict:
        """
        Parse a Tableau workbook file.

        Args:
            workbook_path: Path to .twb or .twbx file
            include_raw_xml: Whether to include raw XML snippets

        Returns:
            Dict with semantic model
        """
        path = Path(workbook_path)

        if not path.exists():
            raise FileNotFoundError(f"Workbook not found: {workbook_path}")

        # Extract XML content
        if path.suffix.lower() == ".twbx":
            xml_content = self._extract_xml_from_twbx(path)
        else:
            with open(path, "r", encoding="utf-8") as f:
                xml_content = f.read()

        # Parse XML
        root = ET.fromstring(xml_content)

        # Build semantic model
        model = SemanticModel()

        # Parse datasources
        model.datasources = self._parse_datasources(root)

        # Parse tables and columns
        model.tables = self._parse_tables(root)

        # Parse relationships
        model.relationships = self._parse_relationships(root)

        # Parse measures (calculated fields)
        model.measures = self._parse_measures(root)

        # Parse parameters
        model.parameters = self._parse_parameters(root)

        # Parse filters
        model.filters = self._parse_filters(root)

        # Parse worksheets/visuals
        model.visuals = self._parse_visuals(root)

        # Parse dashboards
        model.dashboards = self._parse_dashboards(root)

        # Convert to dict
        result = {
            "semantic_model": self._model_to_dict(model),
            "workbook_version": root.get("version", "unknown"),
            "source_file": str(path),
        }

        if include_raw_xml:
            result["raw_xml_snippet"] = xml_content[:5000]

        return result

    def _extract_xml_from_twbx(self, path: Path) -> str:
        """Extract XML content from .twbx (ZIP) file."""
        with zipfile.ZipFile(path, "r") as zf:
            # Find the .twb file inside
            twb_files = [n for n in zf.namelist() if n.endswith(".twb")]
            if not twb_files:
                raise ValueError("No .twb file found in .twbx archive")

            with zf.open(twb_files[0]) as f:
                return f.read().decode("utf-8")

    def _parse_datasources(self, root: ET.Element) -> list[dict]:
        """Parse datasource connections."""
        datasources = []

        for ds in root.findall(".//datasource"):
            ds_info = {
                "name": ds.get("name", ""),
                "caption": ds.get("caption", ds.get("name", "")),
                "connection_type": None,
                "server": None,
                "database": None,
            }

            # Parse connection
            connection = ds.find(".//connection")
            if connection is not None:
                ds_info["connection_type"] = connection.get("class", "unknown")
                ds_info["server"] = connection.get("server")
                ds_info["database"] = connection.get("dbname")
                ds_info["schema"] = connection.get("schema")

            datasources.append(ds_info)

        return datasources

    def _parse_tables(self, root: ET.Element) -> list[Table]:
        """Parse tables and columns."""
        tables = []
        seen_tables = set()

        # Parse from relations
        for relation in root.findall(".//relation"):
            table_name = relation.get("table") or relation.get("name")
            if not table_name or table_name in seen_tables:
                continue

            seen_tables.add(table_name)
            table = Table(
                name=self._clean_name(table_name),
                connection=relation.get("connection"),
            )

            # Get columns from relation
            for col in relation.findall(".//column"):
                column = self._parse_column(col)
                if column:
                    table.columns.append(column)

            tables.append(table)

        # Parse from datasources (columns section)
        for ds in root.findall(".//datasource"):
            ds_name = ds.get("caption") or ds.get("name") or "default"

            # Check if we need to add this as a table
            if ds_name not in seen_tables:
                table = Table(name=self._clean_name(ds_name))
                seen_tables.add(ds_name)

                # Parse columns from datasource
                for col in ds.findall(".//column"):
                    column = self._parse_column(col)
                    if column and column.name not in [c.name for c in table.columns]:
                        table.columns.append(column)

                if table.columns:
                    tables.append(table)

        return tables

    def _parse_column(self, col_elem: ET.Element) -> Optional[Column]:
        """Parse a single column element."""
        name = col_elem.get("name")
        if not name:
            return None

        # Clean brackets from name
        name = self._clean_name(name)

        return Column(
            name=name,
            caption=col_elem.get("caption", name),
            datatype=self.DATATYPE_MAP.get(
                col_elem.get("datatype", "string"), "string"
            ),
            role=col_elem.get("role", "dimension"),
            aggregation=self.AGGREGATION_MAP.get(col_elem.get("aggregation")),
            semantic_role=col_elem.get("semantic-role"),
            calculation=self._extract_calculation(col_elem),
        )

    def _extract_calculation(self, col_elem: ET.Element) -> Optional[str]:
        """Extract calculation formula from column."""
        calc = col_elem.find(".//calculation")
        if calc is not None:
            return calc.get("formula")
        return None

    def _parse_relationships(self, root: ET.Element) -> list[Relationship]:
        """Parse table relationships/joins."""
        relationships = []

        # Parse from object-graph (newer format)
        for rel in root.findall(".//object-graph//relationship"):
            relationships.append(Relationship(
                left_table=self._clean_name(rel.get("left-table", "")),
                right_table=self._clean_name(rel.get("right-table", "")),
                left_column=self._clean_name(rel.get("left-column", "")),
                right_column=self._clean_name(rel.get("right-column", "")),
                relationship_type=rel.get("type", "inner"),
            ))

        # Parse from relations (join clauses)
        for clause in root.findall(".//clause[@type='join']"):
            expression = clause.find(".//expression")
            if expression is not None:
                # Parse join expression
                left = expression.get("left", "")
                right = expression.get("right", "")
                if left and right:
                    left_parts = left.strip("[]").split("].[")
                    right_parts = right.strip("[]").split("].[")
                    if len(left_parts) >= 2 and len(right_parts) >= 2:
                        relationships.append(Relationship(
                            left_table=self._clean_name(left_parts[0]),
                            right_table=self._clean_name(right_parts[0]),
                            left_column=self._clean_name(left_parts[1]),
                            right_column=self._clean_name(right_parts[1]),
                            relationship_type=clause.get("join", "inner"),
                        ))

        return relationships

    def _parse_measures(self, root: ET.Element) -> list[Measure]:
        """Parse calculated fields/measures."""
        measures = []

        for col in root.findall(".//column[@role='measure']"):
            calc = col.find(".//calculation")
            if calc is not None:
                formula = calc.get("formula", "")
                measures.append(Measure(
                    name=self._clean_name(col.get("name", "")),
                    caption=col.get("caption", col.get("name", "")),
                    formula=formula,
                    datatype=self.DATATYPE_MAP.get(
                        col.get("datatype", "real"), "float"
                    ),
                    aggregation=self.AGGREGATION_MAP.get(col.get("aggregation")),
                ))

        # Also parse from calculated-members
        for calc_member in root.findall(".//calculated-member"):
            formula = calc_member.get("formula", "")
            measures.append(Measure(
                name=self._clean_name(calc_member.get("name", "")),
                caption=calc_member.get("caption", calc_member.get("name", "")),
                formula=formula,
                datatype="float",
            ))

        return measures

    def _parse_parameters(self, root: ET.Element) -> list[Parameter]:
        """Parse dashboard parameters."""
        parameters = []

        for param in root.findall(".//parameter"):
            param_obj = Parameter(
                name=self._clean_name(param.get("name", "")),
                caption=param.get("caption", param.get("name", "")),
                datatype=self.DATATYPE_MAP.get(
                    param.get("datatype", "string"), "string"
                ),
                current_value=param.get("current-value"),
            )

            # Parse allowable values
            allowable = param.find(".//allowable-values")
            if allowable is not None:
                if allowable.get("type") == "list":
                    param_obj.allowable_values = [
                        v.get("value")
                        for v in allowable.findall(".//value")
                    ]

            parameters.append(param_obj)

        return parameters

    def _parse_filters(self, root: ET.Element) -> list[Filter]:
        """Parse filters."""
        filters = []

        for filt in root.findall(".//filter"):
            filter_obj = Filter(
                name=filt.get("caption", filt.get("column", "")),
                column=self._clean_name(filt.get("column", "")),
                filter_type="categorical",
                scope="global",
            )

            # Determine filter type
            groupfilter = filt.find(".//groupfilter")
            if groupfilter is not None:
                if groupfilter.get("function") == "range":
                    filter_obj.filter_type = "range"
                    filter_obj.range_min = groupfilter.get("from")
                    filter_obj.range_max = groupfilter.get("to")
                elif groupfilter.get("function") == "member":
                    filter_obj.values = [
                        gf.get("member")
                        for gf in groupfilter.findall(".//groupfilter")
                    ]

            filters.append(filter_obj)

        return filters

    def _parse_visuals(self, root: ET.Element) -> list[Visual]:
        """Parse worksheets/visuals."""
        visuals = []

        for ws in root.findall(".//worksheet"):
            visual = Visual(
                name=ws.get("name", ""),
                title=ws.get("title"),
                visual_type="unknown",
            )

            # Parse table pane for shelf information
            table = ws.find(".//table")
            if table is not None:
                view = table.find(".//view")
                if view is not None:
                    # Get mark type
                    marks = view.find(".//mark")
                    if marks is not None:
                        visual.mark_type = marks.get("class", "automatic")

                    # Determine visual type from mark
                    visual.visual_type = self._infer_visual_type(visual.mark_type)

                # Parse rows shelf
                for row in table.findall(".//rows"):
                    if row.text:
                        visual.rows_shelf = self._parse_shelf_fields(row.text)

                # Parse cols shelf
                for col in table.findall(".//cols"):
                    if col.text:
                        visual.cols_shelf = self._parse_shelf_fields(col.text)

            # Parse datasource-dependencies for columns used
            for dep in ws.findall(".//datasource-dependencies"):
                for col in dep.findall(".//column"):
                    col_name = self._clean_name(col.get("name", ""))
                    if col.get("role") == "measure":
                        if col_name not in visual.measures_used:
                            visual.measures_used.append(col_name)
                    else:
                        if col_name not in visual.columns_used:
                            visual.columns_used.append(col_name)

            # Combine all used fields
            visual.columns_used.extend(visual.rows_shelf)
            visual.columns_used.extend(visual.cols_shelf)
            visual.columns_used = list(set(visual.columns_used))

            visuals.append(visual)

        return visuals

    def _parse_shelf_fields(self, shelf_text: str) -> list[str]:
        """Parse field references from shelf text."""
        # Extract field names from brackets
        fields = re.findall(r'\[([^\]]+)\]', shelf_text)
        return [self._clean_name(f) for f in fields]

    def _infer_visual_type(self, mark_type: Optional[str]) -> str:
        """Infer visual type from mark type."""
        mark_to_visual = {
            "bar": "bar_chart",
            "line": "line_chart",
            "area": "area_chart",
            "circle": "scatter",
            "square": "heatmap",
            "pie": "pie_chart",
            "text": "table",
            "map": "map",
            "ganttbar": "gantt",
            "polygon": "map",
            "automatic": "auto",
        }
        return mark_to_visual.get(mark_type, "unknown")

    def _parse_dashboards(self, root: ET.Element) -> list[Dashboard]:
        """Parse dashboard layouts."""
        dashboards = []

        for db in root.findall(".//dashboard"):
            dashboard = Dashboard(
                name=db.get("name", ""),
                title=db.get("title"),
            )

            # Get size
            size = db.find(".//size")
            if size is not None:
                dashboard.width = int(size.get("maxwidth", 0) or 0)
                dashboard.height = int(size.get("maxheight", 0) or 0)

            # Get worksheets included
            for zone in db.findall(".//zone"):
                ws_name = zone.get("name")
                if ws_name and zone.get("type-v2") == "worksheet":
                    dashboard.worksheets.append(ws_name)

            # Get device layouts
            for device in db.findall(".//devicelayout"):
                device_type = device.get("device-type", "default")
                dashboard.device_layouts.append(device_type)

            dashboards.append(dashboard)

        return dashboards

    def _clean_name(self, name: str) -> str:
        """Clean up field/table names."""
        # Remove brackets
        name = re.sub(r'^\[|\]$', '', name)
        # Remove datasource prefix
        if "].[" in name:
            name = name.split("].[")[-1]
        return name.strip()

    def _model_to_dict(self, model: SemanticModel) -> dict:
        """Convert SemanticModel to serializable dict."""
        return {
            "datasources": model.datasources,
            "tables": [asdict(t) for t in model.tables],
            "relationships": [asdict(r) for r in model.relationships],
            "measures": [asdict(m) for m in model.measures],
            "parameters": [asdict(p) for p in model.parameters],
            "filters": [asdict(f) for f in model.filters],
            "visuals": [asdict(v) for v in model.visuals],
            "dashboards": [asdict(d) for d in model.dashboards],
        }


# =============================================================================
# SKILL HANDLER
# =============================================================================
async def handle(inputs: dict) -> dict:
    """
    Skill handler for parse_tableau_semantic_model.

    Args:
        inputs: Dict with workbook_path, include_raw_xml

    Returns:
        Dict with semantic_model
    """
    workbook_path = inputs.get("workbook_path")
    if not workbook_path:
        raise ValueError("workbook_path is required")

    include_raw_xml = inputs.get("include_raw_xml", False)

    parser = TableauWorkbookParser()
    result = parser.parse_workbook(
        workbook_path=workbook_path,
        include_raw_xml=include_raw_xml
    )

    return result


# =============================================================================
# VALIDATION EXAMPLE
# =============================================================================
VALIDATION_EXAMPLE = {
    "input": {
        "workbook_path": "./workbooks/SalesPerformance.twbx",
        "include_raw_xml": False
    },
    "output": {
        "semantic_model": {
            "datasources": [
                {
                    "name": "Sales Data",
                    "caption": "Sales Data",
                    "connection_type": "postgres",
                    "server": "localhost",
                    "database": "sales_db",
                    "schema": "public"
                }
            ],
            "tables": [
                {
                    "name": "orders",
                    "columns": [
                        {"name": "order_id", "datatype": "integer", "role": "dimension"},
                        {"name": "customer_id", "datatype": "integer", "role": "dimension"},
                        {"name": "order_date", "datatype": "date", "role": "dimension"},
                        {"name": "amount", "datatype": "float", "role": "measure"}
                    ],
                    "connection": "postgres",
                    "schema": "public"
                },
                {
                    "name": "customers",
                    "columns": [
                        {"name": "customer_id", "datatype": "integer", "role": "dimension"},
                        {"name": "customer_name", "datatype": "string", "role": "dimension"},
                        {"name": "segment", "datatype": "string", "role": "dimension"},
                        {"name": "region", "datatype": "string", "role": "dimension"}
                    ],
                    "connection": "postgres",
                    "schema": "public"
                }
            ],
            "relationships": [
                {
                    "left_table": "orders",
                    "right_table": "customers",
                    "left_column": "customer_id",
                    "right_column": "customer_id",
                    "relationship_type": "inner"
                }
            ],
            "measures": [
                {
                    "name": "Total Sales",
                    "caption": "Total Sales",
                    "formula": "SUM([amount])",
                    "datatype": "float",
                    "aggregation": "SUM"
                },
                {
                    "name": "Order Count",
                    "caption": "Order Count",
                    "formula": "COUNT([order_id])",
                    "datatype": "integer",
                    "aggregation": "COUNT"
                },
                {
                    "name": "Avg Order Value",
                    "caption": "Average Order Value",
                    "formula": "[Total Sales] / [Order Count]",
                    "datatype": "float",
                    "aggregation": None
                }
            ],
            "parameters": [],
            "filters": [
                {
                    "name": "Date Range",
                    "column": "order_date",
                    "filter_type": "range",
                    "range_min": "2024-01-01",
                    "range_max": "2024-12-31",
                    "scope": "global"
                }
            ],
            "visuals": [
                {
                    "name": "Sales by Region",
                    "title": "Sales by Region",
                    "visual_type": "bar_chart",
                    "columns_used": ["region", "segment"],
                    "measures_used": ["Total Sales"],
                    "mark_type": "bar",
                    "rows_shelf": ["region"],
                    "cols_shelf": ["Total Sales"]
                },
                {
                    "name": "Sales Trend",
                    "title": "Sales Over Time",
                    "visual_type": "line_chart",
                    "columns_used": ["order_date"],
                    "measures_used": ["Total Sales"],
                    "mark_type": "line",
                    "rows_shelf": ["Total Sales"],
                    "cols_shelf": ["order_date"]
                }
            ],
            "dashboards": [
                {
                    "name": "Sales Dashboard",
                    "title": "Sales Performance Dashboard",
                    "worksheets": ["Sales by Region", "Sales Trend"],
                    "width": 1200,
                    "height": 800,
                    "device_layouts": ["desktop", "tablet"]
                }
            ]
        },
        "workbook_version": "18.1",
        "source_file": "./workbooks/SalesPerformance.twbx"
    }
}


if __name__ == "__main__":
    print(json.dumps(VALIDATION_EXAMPLE, indent=2))
