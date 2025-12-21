# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta


class MonthEndPeriod(models.Model):
    """Month-End Close Period Management"""
    _name = 'ipai.month.end.period'
    _description = 'Month-End Close Period'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_start desc'

    name = fields.Char(
        string='Period Name',
        required=True,
        tracking=True,
        help='e.g., November 2025 Close'
    )
    code = fields.Char(
        string='Period Code',
        required=True,
        help='e.g., 2025-11'
    )
    date_start = fields.Date(
        string='Period Start',
        required=True,
        tracking=True
    )
    date_end = fields.Date(
        string='Period End',
        required=True,
        tracking=True
    )
    close_start_date = fields.Date(
        string='Close Process Start',
        required=True,
        tracking=True,
        help='Date when month-end close activities begin'
    )
    close_deadline = fields.Date(
        string='Close Deadline',
        required=True,
        tracking=True,
        help='Target date for completing the close'
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Start'),
        ('in_progress', 'In Progress'),
        ('review', 'Under Review'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    # Relationships
    task_ids = fields.One2many(
        'ipai.month.end.task',
        'period_id',
        string='Close Tasks'
    )
    checklist_id = fields.Many2one(
        'ipai.month.end.checklist',
        string='Checklist Template'
    )

    # Computed fields
    task_count = fields.Integer(
        string='Total Tasks',
        compute='_compute_task_stats',
        store=True
    )
    completed_count = fields.Integer(
        string='Completed Tasks',
        compute='_compute_task_stats',
        store=True
    )
    progress_percent = fields.Float(
        string='Progress %',
        compute='_compute_task_stats',
        store=True
    )
    overdue_count = fields.Integer(
        string='Overdue Tasks',
        compute='_compute_task_stats',
        store=True
    )

    # Approvals
    approved_by_id = fields.Many2one(
        'res.users',
        string='Approved By',
        tracking=True
    )
    approval_date = fields.Datetime(
        string='Approval Date',
        tracking=True
    )

    # Company
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )

    @api.depends('task_ids', 'task_ids.state', 'task_ids.deadline')
    def _compute_task_stats(self):
        for period in self:
            tasks = period.task_ids
            period.task_count = len(tasks)
            period.completed_count = len(tasks.filtered(lambda t: t.state == 'done'))
            period.progress_percent = (
                (period.completed_count / period.task_count * 100)
                if period.task_count else 0
            )
            today = fields.Date.today()
            period.overdue_count = len(tasks.filtered(
                lambda t: t.state not in ('done', 'cancelled') and t.deadline and t.deadline < today
            ))

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for period in self:
            if period.date_end < period.date_start:
                raise ValidationError('Period end date must be after start date.')

    def action_start_close(self):
        """Begin the month-end close process"""
        self.ensure_one()
        if self.state != 'pending':
            raise UserError('Can only start close from Pending status.')

        # Generate tasks from checklist template
        if self.checklist_id:
            self._generate_tasks_from_checklist()

        self.state = 'in_progress'
        self.message_post(body='Month-end close process started.')
        return True

    def action_submit_review(self):
        """Submit period for final review"""
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError('Can only submit for review when In Progress.')

        # Check for incomplete mandatory tasks
        incomplete = self.task_ids.filtered(
            lambda t: t.is_mandatory and t.state != 'done'
        )
        if incomplete:
            raise UserError(
                f'Cannot submit: {len(incomplete)} mandatory tasks are incomplete.'
            )

        self.state = 'review'
        self.message_post(body='Period submitted for final review.')
        return True

    def action_close_period(self):
        """Close the accounting period"""
        self.ensure_one()
        if self.state != 'review':
            raise UserError('Can only close from Review status.')

        self.write({
            'state': 'closed',
            'approved_by_id': self.env.user.id,
            'approval_date': fields.Datetime.now(),
        })
        self.message_post(body=f'Period closed by {self.env.user.name}.')
        return True

    def action_cancel(self):
        """Cancel the close period"""
        self.ensure_one()
        if self.state == 'closed':
            raise UserError('Cannot cancel a closed period.')
        self.state = 'cancelled'
        self.message_post(body='Period cancelled.')
        return True

    def _generate_tasks_from_checklist(self):
        """Generate period tasks from checklist template"""
        if not self.checklist_id:
            return

        Task = self.env['ipai.month.end.task']
        for template_task in self.checklist_id.task_template_ids:
            # Calculate deadline based on day offset
            deadline = self.close_start_date + timedelta(days=template_task.day_offset)

            Task.create({
                'period_id': self.id,
                'name': template_task.name,
                'description': template_task.description,
                'day_number': template_task.day_offset + 1,
                'scheduled_time': template_task.scheduled_time,
                'deadline': deadline,
                'assigned_user_id': template_task.default_assignee_id.id,
                'raci_responsible_id': template_task.raci_responsible_id.id,
                'raci_accountable_id': template_task.raci_accountable_id.id,
                'is_mandatory': template_task.is_mandatory,
                'sequence': template_task.sequence,
                'task_category': template_task.task_category,
            })
