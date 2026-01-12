#!/usr/bin/env python3
"""
Skill: generate_workflow_automation_template
Intent: Generate Odoo 18 CE/OCA workflow automation templates (cron, server actions, n8n)

Creates automation specifications for:
- Odoo server actions (ir.actions.server)
- Scheduled jobs (ir.cron)
- Automated actions (base.automation)
- BI snapshot models
- n8n workflow templates
"""

import json
import re
from dataclasses import dataclass, field, asdict
from typing import Optional, Any
from datetime import datetime


@dataclass
class OdooServerAction:
    """Odoo ir.actions.server definition."""
    name: str
    model_name: str
    state: str  # code, object_create, object_write, multi
    code: str
    sequence: int = 10
    binding_model_id: Optional[str] = None
    groups_id: list[str] = field(default_factory=list)


@dataclass
class OdooCronJob:
    """Odoo ir.cron scheduled job."""
    name: str
    model_name: str
    method_name: str
    interval_number: int
    interval_type: str  # minutes, hours, days, weeks, months
    numbercall: int = -1  # -1 = unlimited
    doall: bool = False
    active: bool = True
    code: Optional[str] = None


@dataclass
class OdooAutomatedAction:
    """Odoo base.automation rule."""
    name: str
    model_name: str
    trigger: str  # on_create, on_write, on_unlink, on_time
    filter_domain: str
    server_action_id: str
    trigger_field_ids: list[str] = field(default_factory=list)


@dataclass
class BiSnapshotModel:
    """BI snapshot model definition."""
    name: str
    model_name: str
    description: str
    fields: list[dict] = field(default_factory=list)
    sql_view: Optional[str] = None
    source_model: str = ""


@dataclass
class N8nWorkflow:
    """n8n workflow template."""
    name: str
    description: str
    nodes: list[dict] = field(default_factory=list)
    connections: dict = field(default_factory=dict)
    settings: dict = field(default_factory=dict)


class WorkflowAutomationGenerator:
    """Generates Odoo 18 CE/OCA workflow automation templates."""

    # Odoo field type mapping
    FIELD_TYPES = {
        "string": "Char",
        "integer": "Integer",
        "float": "Float",
        "date": "Date",
        "datetime": "Datetime",
        "boolean": "Boolean",
        "many2one": "Many2one",
    }

    def __init__(self):
        self.generated_at = datetime.utcnow().isoformat()

    def generate_templates(
        self,
        odoo_mapping: dict,
        kpis: list[dict],
        automation_type: str = "all"
    ) -> dict:
        """
        Generate Odoo workflow automation templates.

        Args:
            odoo_mapping: Odoo model mapping
            kpis: KPI definitions to automate
            automation_type: Type of automation (cron, on_change, all)

        Returns:
            Dict with server_actions, cron_jobs, automated_actions, bi_snapshots, n8n_workflows
        """
        server_actions = []
        cron_jobs = []
        automated_actions = []
        bi_snapshot_models = []
        n8n_workflows = []

        # Generate BI snapshot models first
        bi_snapshot_models = self._generate_bi_snapshots(odoo_mapping, kpis)

        # Generate server actions for KPI computation
        if automation_type in ["all", "on_change"]:
            server_actions = self._generate_server_actions(odoo_mapping, kpis, bi_snapshot_models)
            automated_actions = self._generate_automated_actions(odoo_mapping, server_actions)

        # Generate cron jobs for periodic snapshots
        if automation_type in ["all", "cron"]:
            cron_jobs = self._generate_cron_jobs(bi_snapshot_models)

        # Generate n8n workflows for external orchestration
        n8n_workflows = self._generate_n8n_workflows(odoo_mapping, kpis, bi_snapshot_models)

        return {
            "workflow_template": {
                "server_actions": [asdict(a) for a in server_actions],
                "cron_jobs": [asdict(c) for c in cron_jobs],
                "automated_actions": [asdict(a) for a in automated_actions],
                "bi_snapshot_models": [asdict(m) for m in bi_snapshot_models],
                "n8n_workflows": [asdict(w) for w in n8n_workflows],
                "generated_at": self.generated_at,
            }
        }

    def _generate_bi_snapshots(
        self,
        odoo_mapping: dict,
        kpis: list[dict]
    ) -> list[BiSnapshotModel]:
        """Generate BI snapshot model definitions."""
        snapshots = []

        # Group KPIs by model
        model_kpis = {}
        for kpi in kpis:
            model = kpi.get("odoo_model", "sale.order")
            if model not in model_kpis:
                model_kpis[model] = []
            model_kpis[model].append(kpi)

        # Generate snapshot model for each source model
        for model, model_kpi_list in model_kpis.items():
            snapshot_name = f"bi.{model.replace('.', '_')}.snapshot"
            snapshot_table = snapshot_name.replace(".", "_")

            # Build fields from KPIs
            fields = [
                {"name": "id", "type": "Integer", "primary_key": True},
                {"name": "snapshot_date", "type": "Date", "required": True, "index": True},
                {"name": "period", "type": "Char", "required": True},
            ]

            # Add dimension fields from entity mapping
            for entity in odoo_mapping.get("entity_mappings", []):
                if entity.get("odoo_model") == model:
                    for fm in entity.get("field_mappings", []):
                        if fm.get("role") == "dimension" or "_id" in fm.get("odoo_field", ""):
                            field_type = self.FIELD_TYPES.get(fm.get("datatype", "string"), "Char")
                            fields.append({
                                "name": fm.get("odoo_field"),
                                "type": field_type,
                                "index": True,
                            })

            # Add KPI fields
            for kpi in model_kpi_list:
                kpi_field_name = self._to_snake_case(kpi.get("name", "metric"))
                fields.append({
                    "name": kpi_field_name,
                    "type": "Float",
                    "digits": (16, 2),
                    "help": kpi.get("description", ""),
                })

            # Generate SQL view for the snapshot
            sql_view = self._generate_snapshot_sql(model, model_kpi_list, odoo_mapping)

            snapshot = BiSnapshotModel(
                name=f"BI Snapshot: {model}",
                model_name=snapshot_name,
                description=f"Daily KPI snapshot for {model}",
                fields=fields,
                sql_view=sql_view,
                source_model=model,
            )
            snapshots.append(snapshot)

        return snapshots

    def _generate_snapshot_sql(
        self,
        model: str,
        kpis: list[dict],
        odoo_mapping: dict
    ) -> str:
        """Generate SQL view for BI snapshot."""
        table_name = model.replace(".", "_")

        # Build SELECT clause
        selects = [
            "DATE_TRUNC('day', create_date)::date as snapshot_date",
            "TO_CHAR(create_date, 'YYYY-MM') as period",
        ]

        # Add dimension columns
        for entity in odoo_mapping.get("entity_mappings", []):
            if entity.get("odoo_model") == model:
                for fm in entity.get("field_mappings", []):
                    if fm.get("role") == "dimension":
                        selects.append(fm.get("odoo_field"))

        # Add KPI expressions
        for kpi in kpis:
            kpi_name = self._to_snake_case(kpi.get("name", "metric"))
            expr = kpi.get("sql_expression", kpi.get("odoo_expression", "0"))
            selects.append(f"{expr} as {kpi_name}")

        # Build GROUP BY
        group_by = ["DATE_TRUNC('day', create_date)", "TO_CHAR(create_date, 'YYYY-MM')"]
        for entity in odoo_mapping.get("entity_mappings", []):
            if entity.get("odoo_model") == model:
                for fm in entity.get("field_mappings", []):
                    if fm.get("role") == "dimension":
                        group_by.append(fm.get("odoo_field"))

        sql = f"""
-- BI Snapshot View for {model}
CREATE OR REPLACE VIEW bi_{table_name}_snapshot AS
SELECT
    {','.join(f'    {s}' for s in selects)}
FROM {table_name}
WHERE create_date >= CURRENT_DATE - INTERVAL '1 year'
GROUP BY {', '.join(group_by)}
ORDER BY snapshot_date DESC;
"""
        return sql.strip()

    def _generate_server_actions(
        self,
        odoo_mapping: dict,
        kpis: list[dict],
        bi_snapshots: list[BiSnapshotModel]
    ) -> list[OdooServerAction]:
        """Generate Odoo server action definitions."""
        actions = []

        for snapshot in bi_snapshots:
            # Generate code for snapshot computation
            code = self._generate_snapshot_action_code(snapshot, kpis)

            action = OdooServerAction(
                name=f"Compute {snapshot.name}",
                model_name=snapshot.source_model,
                state="code",
                code=code,
                sequence=10,
            )
            actions.append(action)

        # Generate alert action for KPI thresholds
        alert_action = OdooServerAction(
            name="Check KPI Thresholds and Alert",
            model_name="sale.order",  # Default model
            state="code",
            code=self._generate_alert_action_code(kpis),
            sequence=20,
        )
        actions.append(alert_action)

        return actions

    def _generate_snapshot_action_code(
        self,
        snapshot: BiSnapshotModel,
        kpis: list[dict]
    ) -> str:
        """Generate Python code for snapshot server action."""
        model_kpis = [k for k in kpis if k.get("odoo_model") == snapshot.source_model]

        code = f'''# Compute {snapshot.name}
from datetime import date, timedelta

snapshot_model = env['{snapshot.model_name}']
source_model = env['{snapshot.source_model}']

# Get today's date
today = date.today()
period = today.strftime('%Y-%m')

# Check if snapshot already exists for today
existing = snapshot_model.search([
    ('snapshot_date', '=', today),
    ('period', '=', period)
], limit=1)

if existing:
    # Update existing snapshot
    snapshot_record = existing
else:
    # Create new snapshot
    snapshot_record = snapshot_model.create({{
        'snapshot_date': today,
        'period': period,
    }})

# Compute KPIs
records = source_model.search([
    ('create_date', '>=', today - timedelta(days=30))
])

'''
        # Add KPI computations
        for kpi in model_kpis:
            kpi_name = self._to_snake_case(kpi.get("name", "metric"))
            expr = kpi.get("odoo_expression", "0")

            # Convert SQL expression to Python/ORM
            if "SUM" in expr.upper():
                field = re.search(r'SUM\((\w+)\)', expr, re.I)
                if field:
                    code += f"kpi_{kpi_name} = sum(r.{field.group(1)} or 0 for r in records)\n"
            elif "COUNT" in expr.upper():
                code += f"kpi_{kpi_name} = len(records)\n"
            elif "AVG" in expr.upper():
                field = re.search(r'AVG\((\w+)\)', expr, re.I)
                if field:
                    code += f"kpi_{kpi_name} = sum(r.{field.group(1)} or 0 for r in records) / max(len(records), 1)\n"
            else:
                code += f"kpi_{kpi_name} = 0  # TODO: implement custom formula\n"

        # Add write statement
        code += "\n# Update snapshot record\nsnapshot_record.write({\n"
        for kpi in model_kpis:
            kpi_name = self._to_snake_case(kpi.get("name", "metric"))
            code += f"    '{kpi_name}': kpi_{kpi_name},\n"
        code += "})\n"

        return code

    def _generate_alert_action_code(self, kpis: list[dict]) -> str:
        """Generate Python code for alert server action."""
        code = '''# Check KPI thresholds and create activities/notifications
from datetime import date

# Define thresholds (customize per KPI)
thresholds = {
'''
        for kpi in kpis[:5]:  # Limit to first 5 KPIs
            kpi_name = self._to_snake_case(kpi.get("name", "metric"))
            code += f"    '{kpi_name}': {{'warning': 1000, 'critical': 500}},\n"

        code += '''}

# Get latest snapshot
snapshot_model = env['bi.sale_order.snapshot']
latest = snapshot_model.search([], order='snapshot_date desc', limit=1)

if latest:
    alerts = []
    for kpi_name, levels in thresholds.items():
        value = getattr(latest, kpi_name, 0)
        if value < levels.get('critical', 0):
            alerts.append(f"CRITICAL: {kpi_name} = {value}")
        elif value < levels.get('warning', 0):
            alerts.append(f"WARNING: {kpi_name} = {value}")

    if alerts:
        # Create activity for admin user
        env['mail.activity'].create({
            'res_model_id': env.ref('sale.model_sale_order').id,
            'res_id': 1,  # Link to first order or config
            'activity_type_id': env.ref('mail.mail_activity_data_todo').id,
            'summary': 'KPI Alert',
            'note': '\\n'.join(alerts),
            'user_id': env.user.id,
        })
'''
        return code

    def _generate_automated_actions(
        self,
        odoo_mapping: dict,
        server_actions: list[OdooServerAction]
    ) -> list[OdooAutomatedAction]:
        """Generate Odoo automated action rules."""
        automated_actions = []

        # Create automated action for each entity mapping
        for entity in odoo_mapping.get("entity_mappings", []):
            model = entity.get("odoo_model")
            if not model:
                continue

            # Find related server action
            related_action = None
            for sa in server_actions:
                if sa.model_name == model:
                    related_action = sa
                    break

            if related_action:
                automated_action = OdooAutomatedAction(
                    name=f"Auto-update BI snapshot on {model} change",
                    model_name=model,
                    trigger="on_write",
                    filter_domain="[('state', 'in', ['sale', 'done'])]" if model == "sale.order" else "[]",
                    server_action_id=related_action.name,
                    trigger_field_ids=["state", "amount_total"] if model == "sale.order" else [],
                )
                automated_actions.append(automated_action)

        return automated_actions

    def _generate_cron_jobs(
        self,
        bi_snapshots: list[BiSnapshotModel]
    ) -> list[OdooCronJob]:
        """Generate Odoo cron job definitions."""
        cron_jobs = []

        for snapshot in bi_snapshots:
            # Daily snapshot cron
            daily_cron = OdooCronJob(
                name=f"Daily {snapshot.name}",
                model_name=snapshot.model_name,
                method_name="_compute_daily_snapshot",
                interval_number=1,
                interval_type="days",
                numbercall=-1,
                active=True,
                code=f'''# Auto-generated cron for {snapshot.name}
model = env['{snapshot.model_name}']
model._compute_daily_snapshot()
''',
            )
            cron_jobs.append(daily_cron)

            # Hourly refresh for real-time dashboards
            hourly_cron = OdooCronJob(
                name=f"Hourly Refresh {snapshot.name}",
                model_name=snapshot.model_name,
                method_name="_refresh_current_day",
                interval_number=1,
                interval_type="hours",
                numbercall=-1,
                active=True,
                code=f'''# Refresh today's snapshot
model = env['{snapshot.model_name}']
model._refresh_current_day()
''',
            )
            cron_jobs.append(hourly_cron)

        return cron_jobs

    def _generate_n8n_workflows(
        self,
        odoo_mapping: dict,
        kpis: list[dict],
        bi_snapshots: list[BiSnapshotModel]
    ) -> list[N8nWorkflow]:
        """Generate n8n workflow templates."""
        workflows = []

        # Workflow 1: KPI Snapshot Pipeline
        snapshot_workflow = N8nWorkflow(
            name="Odoo KPI Snapshot Pipeline",
            description="Compute KPI snapshots and push to Superset",
            nodes=[
                {
                    "name": "Schedule",
                    "type": "n8n-nodes-base.scheduleTrigger",
                    "parameters": {
                        "rule": {"interval": [{"field": "hours", "hoursInterval": 1}]}
                    },
                    "position": [250, 300]
                },
                {
                    "name": "Call Odoo Server Action",
                    "type": "n8n-nodes-base.httpRequest",
                    "parameters": {
                        "url": "={{$env.ODOO_URL}}/web/dataset/call_kw",
                        "method": "POST",
                        "bodyParameters": {
                            "model": bi_snapshots[0].source_model if bi_snapshots else "sale.order",
                            "method": "action_compute_kpi_snapshot",
                            "args": [],
                            "kwargs": {}
                        }
                    },
                    "position": [450, 300]
                },
                {
                    "name": "Query Snapshot Data",
                    "type": "n8n-nodes-base.postgres",
                    "parameters": {
                        "operation": "executeQuery",
                        "query": f"SELECT * FROM {bi_snapshots[0].model_name.replace('.', '_') if bi_snapshots else 'bi_snapshot'} WHERE snapshot_date = CURRENT_DATE"
                    },
                    "position": [650, 300]
                },
                {
                    "name": "Push to Superset",
                    "type": "n8n-nodes-base.httpRequest",
                    "parameters": {
                        "url": "={{$env.SUPERSET_URL}}/api/v1/dataset/{{$env.DATASET_ID}}/refresh",
                        "method": "POST"
                    },
                    "position": [850, 300]
                }
            ],
            connections={
                "Schedule": {"main": [[{"node": "Call Odoo Server Action", "type": "main", "index": 0}]]},
                "Call Odoo Server Action": {"main": [[{"node": "Query Snapshot Data", "type": "main", "index": 0}]]},
                "Query Snapshot Data": {"main": [[{"node": "Push to Superset", "type": "main", "index": 0}]]}
            },
            settings={"executionOrder": "v1"}
        )
        workflows.append(snapshot_workflow)

        # Workflow 2: KPI Alert Pipeline
        alert_workflow = N8nWorkflow(
            name="Odoo KPI Alert Pipeline",
            description="Check KPI thresholds and send alerts",
            nodes=[
                {
                    "name": "Schedule",
                    "type": "n8n-nodes-base.scheduleTrigger",
                    "parameters": {
                        "rule": {"interval": [{"field": "minutes", "minutesInterval": 15}]}
                    },
                    "position": [250, 300]
                },
                {
                    "name": "Query KPIs",
                    "type": "n8n-nodes-base.postgres",
                    "parameters": {
                        "operation": "executeQuery",
                        "query": "SELECT * FROM bi_sale_order_snapshot WHERE snapshot_date = CURRENT_DATE ORDER BY id DESC LIMIT 1"
                    },
                    "position": [450, 300]
                },
                {
                    "name": "Check Thresholds",
                    "type": "n8n-nodes-base.if",
                    "parameters": {
                        "conditions": {
                            "number": [{"value1": "={{$json.total_sales}}", "operation": "smaller", "value2": 1000}]
                        }
                    },
                    "position": [650, 300]
                },
                {
                    "name": "Send Slack Alert",
                    "type": "n8n-nodes-base.slack",
                    "parameters": {
                        "channel": "#alerts",
                        "text": "KPI Alert: Sales below threshold"
                    },
                    "position": [850, 200]
                },
                {
                    "name": "Log OK",
                    "type": "n8n-nodes-base.noOp",
                    "position": [850, 400]
                }
            ],
            connections={
                "Schedule": {"main": [[{"node": "Query KPIs", "type": "main", "index": 0}]]},
                "Query KPIs": {"main": [[{"node": "Check Thresholds", "type": "main", "index": 0}]]},
                "Check Thresholds": {
                    "main": [
                        [{"node": "Send Slack Alert", "type": "main", "index": 0}],
                        [{"node": "Log OK", "type": "main", "index": 0}]
                    ]
                }
            }
        )
        workflows.append(alert_workflow)

        return workflows

    def _to_snake_case(self, text: str) -> str:
        """Convert text to snake_case."""
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', '_', text)
        return text.lower()


# =============================================================================
# SKILL HANDLER
# =============================================================================
async def handle(inputs: dict) -> dict:
    """
    Skill handler for generate_workflow_automation_template.

    Args:
        inputs: Dict with odoo_mapping, kpis, automation_type

    Returns:
        Dict with workflow_template
    """
    odoo_mapping = inputs.get("odoo_mapping")
    if not odoo_mapping:
        raise ValueError("odoo_mapping is required")

    kpis = inputs.get("kpis", [])
    automation_type = inputs.get("automation_type", "all")

    generator = WorkflowAutomationGenerator()
    result = generator.generate_templates(
        odoo_mapping=odoo_mapping,
        kpis=kpis,
        automation_type=automation_type
    )

    return result


# =============================================================================
# VALIDATION EXAMPLE
# =============================================================================
VALIDATION_EXAMPLE = {
    "input": {
        "odoo_mapping": {
            "entity_mappings": [
                {"tableau_entity": "orders", "odoo_model": "sale.order", "field_mappings": []}
            ],
            "kpi_expressions": [
                {"name": "Total Sales", "sql_expression": "SUM(amount_total)", "odoo_model": "sale.order"}
            ]
        },
        "kpis": [
            {"name": "Total Sales", "formula": "SUM([amount])", "odoo_model": "sale.order", "sql_expression": "SUM(amount_total)"}
        ],
        "automation_type": "all"
    },
    "output": {
        "workflow_template": {
            "server_actions": [
                {"name": "Compute BI Snapshot: sale.order", "model_name": "sale.order", "state": "code"}
            ],
            "cron_jobs": [
                {"name": "Daily BI Snapshot: sale.order", "interval_type": "days", "interval_number": 1}
            ],
            "automated_actions": [
                {"name": "Auto-update BI snapshot on sale.order change", "trigger": "on_write"}
            ],
            "bi_snapshot_models": [
                {"model_name": "bi.sale_order.snapshot", "source_model": "sale.order"}
            ],
            "n8n_workflows": [
                {"name": "Odoo KPI Snapshot Pipeline", "description": "Compute KPI snapshots"}
            ]
        }
    }
}


if __name__ == "__main__":
    print(json.dumps(VALIDATION_EXAMPLE, indent=2))
