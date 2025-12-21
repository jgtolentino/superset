# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ApprovalRule(models.Model):
    """Approval Rule Configuration"""
    _name = 'ipai.approval.rule'
    _description = 'Approval Rule'
    _order = 'name'

    name = fields.Char(
        string='Rule Name',
        required=True
    )
    description = fields.Text(
        string='Description'
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )

    # Rule type
    rule_type = fields.Selection([
        ('general', 'General'),
        ('month_end', 'Month-End Close'),
        ('bir_filing', 'BIR Filing'),
        ('payment', 'Payment'),
        ('journal_entry', 'Journal Entry'),
    ], string='Rule Type', default='general', required=True)

    # Stages
    stage_ids = fields.One2many(
        'ipai.approval.stage',
        'rule_id',
        string='Approval Stages'
    )

    # Timing
    approval_timeout_hours = fields.Integer(
        string='Approval Timeout (Hours)',
        default=24,
        help='Hours before escalation if not approved'
    )

    # Conditions
    min_amount = fields.Float(
        string='Minimum Amount',
        help='Only apply rule if amount >= this value'
    )
    max_amount = fields.Float(
        string='Maximum Amount',
        help='Only apply rule if amount <= this value'
    )

    # Company
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    # Statistics
    stage_count = fields.Integer(
        string='Stage Count',
        compute='_compute_stage_count'
    )

    @api.depends('stage_ids')
    def _compute_stage_count(self):
        for rule in self:
            rule.stage_count = len(rule.stage_ids)

    def action_view_stages(self):
        """View approval stages"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Approval Stages',
            'res_model': 'ipai.approval.stage',
            'view_mode': 'tree,form',
            'domain': [('rule_id', '=', self.id)],
            'context': {'default_rule_id': self.id},
        }
