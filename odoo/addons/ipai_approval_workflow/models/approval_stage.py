# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ApprovalStage(models.Model):
    """Approval Stage Template"""
    _name = 'ipai.approval.stage'
    _description = 'Approval Stage'
    _order = 'rule_id, sequence'

    name = fields.Char(
        string='Stage Name',
        required=True
    )
    rule_id = fields.Many2one(
        'ipai.approval.rule',
        string='Approval Rule',
        required=True,
        ondelete='cascade'
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )

    # Approvers
    approver_ids = fields.Many2many(
        'res.users',
        'approval_stage_user_rel',
        'stage_id',
        'user_id',
        string='Approvers'
    )
    approver_group_id = fields.Many2one(
        'res.groups',
        string='Approver Group',
        help='All users in this group can approve'
    )

    # RACI mapping
    raci_role = fields.Selection([
        ('responsible', 'Responsible (R)'),
        ('accountable', 'Accountable (A)'),
        ('consulted', 'Consulted (C)'),
        ('informed', 'Informed (I)'),
    ], string='RACI Role', default='accountable')

    # Stage behavior
    approval_mode = fields.Selection([
        ('any', 'Any One Approver'),
        ('all', 'All Approvers'),
        ('majority', 'Majority'),
    ], string='Approval Mode', default='any')

    is_optional = fields.Boolean(
        string='Optional Stage',
        default=False,
        help='Can be skipped if no approvers available'
    )

    # Notifications
    notify_on_pending = fields.Boolean(
        string='Notify When Pending',
        default=True
    )
    notify_on_complete = fields.Boolean(
        string='Notify When Complete',
        default=True
    )

    @api.onchange('approver_group_id')
    def _onchange_approver_group(self):
        """Suggest approvers from group"""
        if self.approver_group_id:
            self.approver_ids = self.approver_group_id.users
