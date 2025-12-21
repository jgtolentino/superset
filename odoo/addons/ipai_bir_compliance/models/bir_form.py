# -*- coding: utf-8 -*-
from odoo import models, fields, api


class BIRForm(models.Model):
    """BIR Form Type Definition"""
    _name = 'ipai.bir.form'
    _description = 'BIR Form Type'
    _order = 'code'

    name = fields.Char(
        string='Form Name',
        required=True
    )
    code = fields.Char(
        string='Form Code',
        required=True,
        help='e.g., 1601-C, 2550M'
    )
    description = fields.Text(
        string='Description'
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )

    # Form properties
    form_type = fields.Selection([
        ('withholding', 'Withholding Tax'),
        ('vat', 'Value Added Tax'),
        ('income', 'Income Tax'),
        ('certificate', 'Certificate'),
        ('annual', 'Annual Return'),
        ('other', 'Other'),
    ], string='Form Type', required=True, default='other')

    frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
        ('on_demand', 'On Demand'),
    ], string='Filing Frequency', default='monthly')

    # Due date calculation
    due_day = fields.Integer(
        string='Due Day of Month',
        default=10,
        help='Day of month when filing is due'
    )
    due_month_offset = fields.Integer(
        string='Due Month Offset',
        default=1,
        help='Months after period end when filing is due'
    )

    # Required fields tracking
    required_data = fields.Text(
        string='Required Data Fields',
        help='Comma-separated list of required data fields'
    )

    # Approval rule
    approval_rule_id = fields.Many2one(
        'ipai.approval.rule',
        string='Approval Rule',
        domain="[('rule_type', '=', 'bir_filing')]"
    )

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Form code must be unique'),
    ]

    def name_get(self):
        result = []
        for record in self:
            name = f"{record.code} - {record.name}"
            result.append((record.id, name))
        return result


class BIRFormLine(models.Model):
    """BIR Form Line Item Definition"""
    _name = 'ipai.bir.form.line'
    _description = 'BIR Form Line Definition'
    _order = 'form_id, sequence'

    form_id = fields.Many2one(
        'ipai.bir.form',
        string='BIR Form',
        required=True,
        ondelete='cascade'
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    line_code = fields.Char(
        string='Line Code',
        required=True,
        help='e.g., 15A, 16B'
    )
    name = fields.Char(
        string='Description',
        required=True
    )
    field_type = fields.Selection([
        ('amount', 'Amount'),
        ('rate', 'Rate/Percentage'),
        ('text', 'Text'),
        ('date', 'Date'),
        ('tin', 'TIN'),
        ('computed', 'Computed'),
    ], string='Field Type', default='amount')

    computation = fields.Char(
        string='Computation Formula',
        help='Formula for computed fields, e.g., "15A + 15B"'
    )
    is_required = fields.Boolean(
        string='Required',
        default=True
    )
