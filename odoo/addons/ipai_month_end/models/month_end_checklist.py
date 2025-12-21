# -*- coding: utf-8 -*-
from odoo import models, fields, api


class MonthEndChecklist(models.Model):
    """Checklist template for month-end close processes"""
    _name = 'ipai.month.end.checklist'
    _description = 'Month-End Checklist Template'
    _order = 'name'

    name = fields.Char(
        string='Checklist Name',
        required=True,
        help='e.g., Standard Month-End Close, Quarter-End Close'
    )
    description = fields.Text(
        string='Description'
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )

    # Task templates
    task_template_ids = fields.One2many(
        'ipai.month.end.task.template',
        'checklist_id',
        string='Task Templates'
    )

    # Statistics
    task_count = fields.Integer(
        string='Task Count',
        compute='_compute_task_count'
    )

    # Company
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    @api.depends('task_template_ids')
    def _compute_task_count(self):
        for checklist in self:
            checklist.task_count = len(checklist.task_template_ids)

    def action_view_tasks(self):
        """View task templates"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Task Templates',
            'res_model': 'ipai.month.end.task.template',
            'view_mode': 'tree,form',
            'domain': [('checklist_id', '=', self.id)],
            'context': {'default_checklist_id': self.id},
        }
