#!/usr/bin/env python3
"""
Skill: map_tableau_to_odoo_models
Intent: Map Tableau semantic model entities to Odoo 18 CE + OCA data models

Maps Tableau entities (tables, measures, fields) to corresponding Odoo models,
fields, and KPI expressions.
"""

import json
import re
from dataclasses import dataclass, field, asdict
from typing import Optional, Any


# =============================================================================
# ODOO 18 CE + OCA MODEL DEFINITIONS
# =============================================================================
ODOO_MODELS = {
    # Core CRM
    "res.partner": {
        "description": "Customers, Vendors, Contacts",
        "key_fields": ["name", "email", "phone", "company_type", "country_id", "state_id", "city"],
        "aliases": ["customer", "vendor", "contact", "partner", "client", "supplier", "account"],
        "domain": "crm",
    },
    "crm.lead": {
        "description": "Sales Pipeline, Opportunities",
        "key_fields": ["name", "expected_revenue", "probability", "stage_id", "partner_id", "user_id", "date_deadline"],
        "aliases": ["lead", "opportunity", "pipeline", "prospect", "deal"],
        "domain": "crm",
    },

    # Sales
    "sale.order": {
        "description": "Sales Orders (Headers)",
        "key_fields": ["name", "partner_id", "date_order", "amount_total", "amount_untaxed", "state", "user_id"],
        "aliases": ["sales_order", "order", "so", "sales_header", "order_header"],
        "domain": "sales",
    },
    "sale.order.line": {
        "description": "Sales Order Lines (Details)",
        "key_fields": ["order_id", "product_id", "product_uom_qty", "price_unit", "price_subtotal", "discount"],
        "aliases": ["order_line", "sales_detail", "order_detail", "line_item", "order_item"],
        "domain": "sales",
    },

    # Products
    "product.template": {
        "description": "Product Templates",
        "key_fields": ["name", "list_price", "standard_price", "categ_id", "type", "default_code"],
        "aliases": ["product", "item", "sku", "article", "goods"],
        "domain": "inventory",
    },
    "product.product": {
        "description": "Product Variants",
        "key_fields": ["product_tmpl_id", "barcode", "default_code", "qty_available", "virtual_available"],
        "aliases": ["product_variant", "variant", "item"],
        "domain": "inventory",
    },
    "product.category": {
        "description": "Product Categories",
        "key_fields": ["name", "parent_id", "complete_name"],
        "aliases": ["category", "product_category", "item_category", "product_group"],
        "domain": "inventory",
    },

    # Accounting
    "account.move": {
        "description": "Journal Entries, Invoices",
        "key_fields": ["name", "partner_id", "invoice_date", "amount_total", "amount_residual", "state", "move_type"],
        "aliases": ["invoice", "bill", "journal_entry", "accounting_entry", "ar", "ap"],
        "domain": "finance",
    },
    "account.move.line": {
        "description": "Journal Entry Lines",
        "key_fields": ["move_id", "account_id", "debit", "credit", "balance", "product_id", "partner_id"],
        "aliases": ["journal_line", "invoice_line", "accounting_line", "gl_line"],
        "domain": "finance",
    },
    "account.payment": {
        "description": "Payments",
        "key_fields": ["name", "partner_id", "amount", "payment_date", "payment_type", "state"],
        "aliases": ["payment", "receipt", "disbursement"],
        "domain": "finance",
    },
    "account.account": {
        "description": "Chart of Accounts",
        "key_fields": ["code", "name", "account_type", "reconcile"],
        "aliases": ["account", "gl_account", "ledger_account", "coa"],
        "domain": "finance",
    },

    # Inventory / Logistics
    "stock.picking": {
        "description": "Stock Transfers, Shipments",
        "key_fields": ["name", "partner_id", "scheduled_date", "state", "picking_type_id", "origin"],
        "aliases": ["shipment", "delivery", "transfer", "picking", "receipt", "shipping"],
        "domain": "inventory",
    },
    "stock.move": {
        "description": "Stock Moves",
        "key_fields": ["picking_id", "product_id", "product_uom_qty", "quantity_done", "state", "location_id", "location_dest_id"],
        "aliases": ["stock_move", "inventory_move", "movement"],
        "domain": "inventory",
    },
    "stock.quant": {
        "description": "Stock Quantities",
        "key_fields": ["product_id", "location_id", "quantity", "reserved_quantity"],
        "aliases": ["stock_level", "inventory_level", "on_hand", "stock_quantity"],
        "domain": "inventory",
    },
    "stock.warehouse": {
        "description": "Warehouses",
        "key_fields": ["name", "code", "partner_id"],
        "aliases": ["warehouse", "location", "depot", "distribution_center"],
        "domain": "inventory",
    },

    # Purchase
    "purchase.order": {
        "description": "Purchase Orders",
        "key_fields": ["name", "partner_id", "date_order", "amount_total", "state"],
        "aliases": ["purchase_order", "po", "procurement"],
        "domain": "purchasing",
    },
    "purchase.order.line": {
        "description": "Purchase Order Lines",
        "key_fields": ["order_id", "product_id", "product_qty", "price_unit", "price_subtotal"],
        "aliases": ["po_line", "purchase_line"],
        "domain": "purchasing",
    },

    # HR (OCA)
    "hr.employee": {
        "description": "Employees",
        "key_fields": ["name", "department_id", "job_id", "work_email", "work_phone"],
        "aliases": ["employee", "staff", "worker", "personnel"],
        "domain": "hr",
    },
    "hr.department": {
        "description": "Departments",
        "key_fields": ["name", "parent_id", "manager_id"],
        "aliases": ["department", "division", "team", "business_unit"],
        "domain": "hr",
    },

    # Project
    "project.project": {
        "description": "Projects",
        "key_fields": ["name", "partner_id", "user_id", "date_start", "date"],
        "aliases": ["project", "job", "engagement"],
        "domain": "project",
    },
    "project.task": {
        "description": "Tasks",
        "key_fields": ["name", "project_id", "user_ids", "date_deadline", "stage_id"],
        "aliases": ["task", "activity", "work_item", "ticket"],
        "domain": "project",
    },
}

# Field type mappings
FIELD_TYPE_MAP = {
    "string": "Char",
    "integer": "Integer",
    "float": "Float",
    "date": "Date",
    "datetime": "Datetime",
    "boolean": "Boolean",
    "text": "Text",
    "html": "Html",
    "binary": "Binary",
    "selection": "Selection",
    "many2one": "Many2one",
    "one2many": "One2many",
    "many2many": "Many2many",
}

# Common KPI patterns
KPI_PATTERNS = {
    "revenue": {
        "models": ["sale.order", "account.move"],
        "expressions": {
            "sale.order": "SUM(amount_total)",
            "account.move": "SUM(amount_total) WHERE move_type IN ('out_invoice', 'out_refund')",
        },
    },
    "sales": {
        "models": ["sale.order", "sale.order.line"],
        "expressions": {
            "sale.order": "SUM(amount_total)",
            "sale.order.line": "SUM(price_subtotal)",
        },
    },
    "quantity": {
        "models": ["sale.order.line", "stock.move"],
        "expressions": {
            "sale.order.line": "SUM(product_uom_qty)",
            "stock.move": "SUM(quantity_done)",
        },
    },
    "profit": {
        "models": ["sale.order.line"],
        "expressions": {
            "sale.order.line": "SUM(price_subtotal) - SUM(purchase_price * product_uom_qty)",
        },
    },
    "margin": {
        "models": ["sale.order.line"],
        "expressions": {
            "sale.order.line": "(SUM(price_subtotal) - SUM(purchase_price * product_uom_qty)) / NULLIF(SUM(price_subtotal), 0)",
        },
    },
    "count": {
        "models": ["sale.order", "crm.lead", "account.move"],
        "expressions": {
            "sale.order": "COUNT(id)",
            "crm.lead": "COUNT(id)",
            "account.move": "COUNT(id)",
        },
    },
    "average": {
        "models": ["sale.order"],
        "expressions": {
            "sale.order": "AVG(amount_total)",
        },
    },
}


@dataclass
class EntityMapping:
    """Maps a Tableau entity to Odoo model."""
    tableau_entity: str
    odoo_model: str
    confidence: float
    field_mappings: list[dict] = field(default_factory=list)
    reasoning: str = ""


@dataclass
class KPIExpression:
    """KPI expressed in Odoo terms."""
    name: str
    tableau_formula: str
    odoo_model: str
    odoo_expression: str
    sql_expression: str
    description: str = ""


@dataclass
class BiView:
    """Recommended BI view for Superset."""
    view_name: str
    base_model: str
    sql: str
    description: str = ""


class OdooMapper:
    """Maps Tableau semantic model to Odoo 18 CE + OCA models."""

    def __init__(self):
        self.models = ODOO_MODELS
        self.kpi_patterns = KPI_PATTERNS

    def map_semantic_model(
        self,
        semantic_model: dict,
        domain_hint: Optional[str] = None,
        custom_mappings: Optional[dict] = None
    ) -> dict:
        """
        Map Tableau semantic model to Odoo models.

        Args:
            semantic_model: Parsed Tableau semantic model
            domain_hint: Business domain hint (sales, finance, inventory, crm)
            custom_mappings: Custom entity-to-model mappings

        Returns:
            Dict with entity_mappings, field_mappings, kpi_expressions
        """
        # Detect domain if not provided
        if not domain_hint:
            domain_hint = self._detect_domain(semantic_model)

        # Initialize result
        entity_mappings = []
        field_mappings = []
        kpi_expressions = []
        suggested_views = []
        assumptions = []

        # Map tables to Odoo models
        for table in semantic_model.get("tables", []):
            mapping = self._map_table_to_model(
                table,
                domain_hint,
                custom_mappings
            )
            if mapping:
                entity_mappings.append(asdict(mapping))
                field_mappings.extend(mapping.field_mappings)

        # Map measures to KPI expressions
        for measure in semantic_model.get("measures", []):
            kpi = self._map_measure_to_kpi(
                measure,
                entity_mappings,
                domain_hint
            )
            if kpi:
                kpi_expressions.append(asdict(kpi))

        # Generate suggested BI views
        suggested_views = self._generate_bi_views(
            entity_mappings,
            kpi_expressions,
            semantic_model
        )

        # Document assumptions
        assumptions = self._document_assumptions(
            entity_mappings,
            semantic_model,
            domain_hint
        )

        return {
            "odoo_mapping": {
                "entity_mappings": entity_mappings,
                "field_mappings": field_mappings,
                "kpi_expressions": kpi_expressions,
                "suggested_views": suggested_views,
                "assumptions": assumptions,
                "detected_domain": domain_hint,
            }
        }

    def _detect_domain(self, semantic_model: dict) -> str:
        """Detect business domain from semantic model content."""
        # Collect all names for analysis
        names = []
        for table in semantic_model.get("tables", []):
            names.append(table.get("name", "").lower())
            for col in table.get("columns", []):
                names.append(col.get("name", "").lower())

        for measure in semantic_model.get("measures", []):
            names.append(measure.get("name", "").lower())
            names.append(measure.get("caption", "").lower())

        text = " ".join(names)

        # Score domains
        domain_scores = {
            "sales": len(re.findall(r"sales?|order|revenue|customer|deal", text)),
            "finance": len(re.findall(r"invoice|payment|account|journal|gl|ar|ap|financial", text)),
            "inventory": len(re.findall(r"stock|inventory|warehouse|product|item|sku|quantity", text)),
            "crm": len(re.findall(r"lead|opportunity|pipeline|prospect|campaign", text)),
            "hr": len(re.findall(r"employee|staff|department|payroll|salary|hire", text)),
            "purchasing": len(re.findall(r"purchase|procurement|vendor|supplier|po", text)),
        }

        return max(domain_scores, key=domain_scores.get)

    def _map_table_to_model(
        self,
        table: dict,
        domain_hint: str,
        custom_mappings: Optional[dict]
    ) -> Optional[EntityMapping]:
        """Map a Tableau table to an Odoo model."""
        table_name = table.get("name", "").lower()

        # Check custom mappings first
        if custom_mappings and table_name in custom_mappings:
            odoo_model = custom_mappings[table_name]
            return EntityMapping(
                tableau_entity=table.get("name"),
                odoo_model=odoo_model,
                confidence=1.0,
                field_mappings=self._map_fields(table, odoo_model),
                reasoning="Custom mapping provided",
            )

        # Score each model for match
        best_match = None
        best_score = 0

        for model_name, model_info in self.models.items():
            score = 0

            # Check aliases
            for alias in model_info.get("aliases", []):
                if alias in table_name or table_name in alias:
                    score += 10
                if alias == table_name:
                    score += 20

            # Check domain match
            if model_info.get("domain") == domain_hint:
                score += 5

            # Check column name matches
            table_cols = {c.get("name", "").lower() for c in table.get("columns", [])}
            model_fields = set(f.lower() for f in model_info.get("key_fields", []))
            col_overlap = len(table_cols & model_fields)
            score += col_overlap * 3

            if score > best_score:
                best_score = score
                best_match = model_name

        if best_match and best_score > 5:
            return EntityMapping(
                tableau_entity=table.get("name"),
                odoo_model=best_match,
                confidence=min(best_score / 30, 1.0),
                field_mappings=self._map_fields(table, best_match),
                reasoning=f"Matched by alias/field similarity (score: {best_score})",
            )

        return None

    def _map_fields(self, table: dict, odoo_model: str) -> list[dict]:
        """Map table columns to Odoo model fields."""
        field_mappings = []
        model_info = self.models.get(odoo_model, {})
        model_fields = model_info.get("key_fields", [])

        for col in table.get("columns", []):
            col_name = col.get("name", "").lower()
            best_field = None

            # Direct match
            for field in model_fields:
                if col_name == field.lower() or col_name.replace("_", "") == field.replace("_", "").lower():
                    best_field = field
                    break

            # Partial match
            if not best_field:
                for field in model_fields:
                    if col_name in field.lower() or field.lower() in col_name:
                        best_field = field
                        break

            if best_field:
                field_mappings.append({
                    "tableau_column": col.get("name"),
                    "odoo_field": best_field,
                    "datatype": col.get("datatype"),
                    "role": col.get("role"),
                })

        return field_mappings

    def _map_measure_to_kpi(
        self,
        measure: dict,
        entity_mappings: list[dict],
        domain_hint: str
    ) -> Optional[KPIExpression]:
        """Map a Tableau measure to an Odoo KPI expression."""
        measure_name = measure.get("name", "").lower()
        formula = measure.get("formula", "")
        caption = measure.get("caption", measure.get("name", ""))

        # Determine base model from entity mappings
        base_model = None
        for mapping in entity_mappings:
            if mapping.get("confidence", 0) > 0.5:
                base_model = mapping.get("odoo_model")
                break

        if not base_model:
            # Default based on domain
            domain_models = {
                "sales": "sale.order",
                "finance": "account.move",
                "inventory": "stock.move",
                "crm": "crm.lead",
                "hr": "hr.employee",
                "purchasing": "purchase.order",
            }
            base_model = domain_models.get(domain_hint, "sale.order")

        # Convert Tableau formula to Odoo SQL
        odoo_expr, sql_expr = self._convert_formula(formula, base_model)

        return KPIExpression(
            name=caption,
            tableau_formula=formula,
            odoo_model=base_model,
            odoo_expression=odoo_expr,
            sql_expression=sql_expr,
            description=f"Converted from Tableau measure: {measure_name}",
        )

    def _convert_formula(self, formula: str, base_model: str) -> tuple[str, str]:
        """Convert Tableau formula to Odoo expression and SQL."""
        # Extract aggregation and field
        agg_match = re.match(r"(SUM|AVG|COUNT|COUNTD?|MIN|MAX)\s*\(\s*\[([^\]]+)\]\s*\)", formula, re.I)

        if agg_match:
            agg_func = agg_match.group(1).upper()
            field_name = agg_match.group(2)

            # Map aggregation
            if agg_func == "COUNTD":
                agg_func = "COUNT_DISTINCT"

            # Map field to Odoo field
            odoo_field = self._map_field_name(field_name, base_model)

            if agg_func == "COUNT_DISTINCT":
                odoo_expr = f"COUNT(DISTINCT {odoo_field})"
                sql_expr = f"COUNT(DISTINCT {odoo_field})"
            else:
                odoo_expr = f"{agg_func}({odoo_field})"
                sql_expr = f"{agg_func}({odoo_field})"

            return odoo_expr, sql_expr

        # Handle calculated fields (division, etc.)
        if "/" in formula:
            parts = formula.split("/")
            if len(parts) == 2:
                left = self._convert_formula(parts[0].strip(), base_model)
                right = self._convert_formula(parts[1].strip(), base_model)
                return (
                    f"({left[0]}) / NULLIF({right[0]}, 0)",
                    f"({left[1]}) / NULLIF({right[1]}, 0)"
                )

        # Default: return as-is with field mapping
        odoo_field = self._map_field_name(formula.strip("[]"), base_model)
        return odoo_field, odoo_field

    def _map_field_name(self, field_name: str, base_model: str) -> str:
        """Map Tableau field name to Odoo field."""
        field_lower = field_name.lower().replace(" ", "_")

        # Common mappings
        common_maps = {
            "amount": "amount_total",
            "total": "amount_total",
            "quantity": "product_uom_qty",
            "qty": "product_uom_qty",
            "price": "price_unit",
            "date": "date_order",
            "customer": "partner_id",
            "product": "product_id",
            "order_id": "id",
            "sales": "amount_total",
            "revenue": "amount_total",
        }

        return common_maps.get(field_lower, field_lower)

    def _generate_bi_views(
        self,
        entity_mappings: list[dict],
        kpi_expressions: list[dict],
        semantic_model: dict
    ) -> list[dict]:
        """Generate recommended BI views for Superset."""
        views = []

        # Group KPIs by base model
        model_kpis = {}
        for kpi in kpi_expressions:
            model = kpi.get("odoo_model")
            if model not in model_kpis:
                model_kpis[model] = []
            model_kpis[model].append(kpi)

        # Generate view for each model
        for model, kpis in model_kpis.items():
            view_name = f"bi_{model.replace('.', '_')}_summary"
            sql_selects = []
            sql_groups = []

            # Add dimension columns
            model_info = self.models.get(model, {})
            for field in model_info.get("key_fields", [])[:5]:
                if "_id" not in field and field not in ["name"]:
                    sql_selects.append(field)
                    sql_groups.append(field)

            # Add date dimension
            date_field = "date_order" if "date_order" in model_info.get("key_fields", []) else "create_date"
            sql_selects.insert(0, f"DATE_TRUNC('month', {date_field}) as period")
            sql_groups.insert(0, f"DATE_TRUNC('month', {date_field})")

            # Add KPI measures
            for kpi in kpis:
                sql_expr = kpi.get("sql_expression", "")
                kpi_name = kpi.get("name", "").lower().replace(" ", "_")
                sql_selects.append(f"{sql_expr} as {kpi_name}")

            sql = f"""
CREATE OR REPLACE VIEW {view_name} AS
SELECT
    {', '.join(sql_selects)}
FROM {model.replace('.', '_')}
GROUP BY {', '.join(sql_groups)};
"""
            views.append({
                "view_name": view_name,
                "base_model": model,
                "sql": sql.strip(),
                "description": f"BI summary view for {model}",
            })

        return views

    def _document_assumptions(
        self,
        entity_mappings: list[dict],
        semantic_model: dict,
        domain_hint: str
    ) -> list[str]:
        """Document mapping assumptions."""
        assumptions = [
            f"Detected business domain: {domain_hint}",
            "Odoo 18 CE + OCA module stack assumed",
            "All Odoo models use standard field names",
        ]

        # Note low-confidence mappings
        for mapping in entity_mappings:
            if mapping.get("confidence", 0) < 0.7:
                assumptions.append(
                    f"Low confidence mapping: {mapping.get('tableau_entity')} → "
                    f"{mapping.get('odoo_model')} ({mapping.get('confidence'):.0%})"
                )

        # Note unmapped tables
        mapped_tables = {m.get("tableau_entity") for m in entity_mappings}
        for table in semantic_model.get("tables", []):
            if table.get("name") not in mapped_tables:
                assumptions.append(f"Unmapped table: {table.get('name')}")

        return assumptions


# =============================================================================
# SKILL HANDLER
# =============================================================================
async def handle(inputs: dict) -> dict:
    """
    Skill handler for map_tableau_to_odoo_models.

    Args:
        inputs: Dict with semantic_model, domain_hint, custom_mappings

    Returns:
        Dict with odoo_mapping
    """
    semantic_model = inputs.get("semantic_model")
    if not semantic_model:
        raise ValueError("semantic_model is required")

    domain_hint = inputs.get("domain_hint")
    custom_mappings = inputs.get("custom_mappings")

    mapper = OdooMapper()
    result = mapper.map_semantic_model(
        semantic_model=semantic_model,
        domain_hint=domain_hint,
        custom_mappings=custom_mappings
    )

    return result


# =============================================================================
# VALIDATION EXAMPLE
# =============================================================================
VALIDATION_EXAMPLE = {
    "input": {
        "semantic_model": {
            "tables": [
                {
                    "name": "orders",
                    "columns": [
                        {"name": "order_id", "datatype": "integer", "role": "dimension"},
                        {"name": "customer_id", "datatype": "integer", "role": "dimension"},
                        {"name": "order_date", "datatype": "date", "role": "dimension"},
                        {"name": "amount", "datatype": "float", "role": "measure"}
                    ]
                },
                {
                    "name": "customers",
                    "columns": [
                        {"name": "customer_id", "datatype": "integer", "role": "dimension"},
                        {"name": "name", "datatype": "string", "role": "dimension"},
                        {"name": "segment", "datatype": "string", "role": "dimension"}
                    ]
                }
            ],
            "measures": [
                {"name": "Total Sales", "caption": "Total Sales", "formula": "SUM([amount])"},
                {"name": "Order Count", "caption": "Order Count", "formula": "COUNT([order_id])"}
            ]
        },
        "domain_hint": "sales"
    },
    "output": {
        "odoo_mapping": {
            "entity_mappings": [
                {
                    "tableau_entity": "orders",
                    "odoo_model": "sale.order",
                    "confidence": 0.9,
                    "field_mappings": [
                        {"tableau_column": "order_id", "odoo_field": "id"},
                        {"tableau_column": "customer_id", "odoo_field": "partner_id"},
                        {"tableau_column": "order_date", "odoo_field": "date_order"},
                        {"tableau_column": "amount", "odoo_field": "amount_total"}
                    ],
                    "reasoning": "Matched by alias/field similarity"
                },
                {
                    "tableau_entity": "customers",
                    "odoo_model": "res.partner",
                    "confidence": 0.85,
                    "field_mappings": [
                        {"tableau_column": "customer_id", "odoo_field": "id"},
                        {"tableau_column": "name", "odoo_field": "name"}
                    ],
                    "reasoning": "Matched by alias/field similarity"
                }
            ],
            "field_mappings": [
                {"tableau_column": "order_id", "odoo_field": "id"},
                {"tableau_column": "amount", "odoo_field": "amount_total"}
            ],
            "kpi_expressions": [
                {
                    "name": "Total Sales",
                    "tableau_formula": "SUM([amount])",
                    "odoo_model": "sale.order",
                    "odoo_expression": "SUM(amount_total)",
                    "sql_expression": "SUM(amount_total)"
                },
                {
                    "name": "Order Count",
                    "tableau_formula": "COUNT([order_id])",
                    "odoo_model": "sale.order",
                    "odoo_expression": "COUNT(id)",
                    "sql_expression": "COUNT(id)"
                }
            ],
            "suggested_views": [
                {
                    "view_name": "bi_sale_order_summary",
                    "base_model": "sale.order",
                    "sql": "CREATE OR REPLACE VIEW bi_sale_order_summary AS...",
                    "description": "BI summary view for sale.order"
                }
            ],
            "assumptions": [
                "Detected business domain: sales",
                "Odoo 18 CE + OCA module stack assumed"
            ],
            "detected_domain": "sales"
        }
    }
}


if __name__ == "__main__":
    print(json.dumps(VALIDATION_EXAMPLE, indent=2))
