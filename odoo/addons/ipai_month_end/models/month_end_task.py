# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class MonthEndTask(models.Model):
    """Individual Month-End Close Task"""
    _name = 'ipai.month.end.task'
    _description = 'Month-End Close Task'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'day_number, scheduled_time, sequence'

    name = fields.Char(
        string='Task Name',
        required=True,
        tracking=True
    )
    description = fields.Html(
        string='Description'
    )
    period_id = fields.Many2one(
        'ipai.month.end.period',
        string='Close Period',
        required=True,
        ondelete='cascade'
    )

    # Scheduling
    day_number = fields.Integer(
        string='Day #',
        required=True,
        help='Day number in the close process (1-10)'
    )
    scheduled_time = fields.Char(
        string='Scheduled Time',
        help='e.g., 08:00, 14:00'
    )
    deadline = fields.Date(
        string='Deadline',
        required=True,
        tracking=True
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )

    # Assignment (RACI)
    assigned_user_id = fields.Many2one(
        'res.users',
        string='Assigned To',
        tracking=True
    )
    raci_responsible_id = fields.Many2one(
        'res.users',
        string='Responsible (R)',
        tracking=True,
        help='Person who does the work'
    )
    raci_accountable_id = fields.Many2one(
        'res.users',
        string='Accountable (A)',
        tracking=True,
        help='Person who approves/signs off'
    )
    raci_consulted_ids = fields.Many2many(
        'res.users',
        'month_end_task_consulted_rel',
        'task_id',
        'user_id',
        string='Consulted (C)',
        help='People who provide input'
    )
    raci_informed_ids = fields.Many2many(
        'res.users',
        'month_end_task_informed_rel',
        'task_id',
        'user_id',
        string='Informed (I)',
        help='People who are kept updated'
    )

    # Status
    state = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('blocked', 'Blocked'),
        ('review', 'Under Review'),
        ('done', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='pending', tracking=True)

    # Task properties
    is_mandatory = fields.Boolean(
        string='Mandatory',
        default=True,
        help='Must be completed before period can be closed'
    )
    task_category = fields.Selection([
        ('payroll', 'Payroll'),
        ('vat', 'VAT/Tax'),
        ('accruals', 'Accruals'),
        ('liquidations', 'Liquidations'),
        ('wip', 'WIP Management'),
        ('treasury', 'Treasury/FX'),
        ('reconciliation', 'Reconciliation'),
        ('reporting', 'Reporting'),
        ('review', 'Review/Approval'),
        ('filing', 'Filing/Compliance'),
        ('other', 'Other'),
    ], string='Category', default='other')

    # Completion tracking
    completed_date = fields.Datetime(
        string='Completed Date',
        tracking=True
    )
    completed_by_id = fields.Many2one(
        'res.users',
        string='Completed By',
        tracking=True
    )
    notes = fields.Text(
        string='Completion Notes'
    )

    # Approval integration
    approval_request_id = fields.Many2one(
        'ipai.approval.request',
        string='Approval Request'
    )

    # Computed
    is_overdue = fields.Boolean(
        string='Overdue',
        compute='_compute_is_overdue',
        store=True
    )

    @api.depends('deadline', 'state')
    def _compute_is_overdue(self):
        today = fields.Date.today()
        for task in self:
            task.is_overdue = (
                task.state not in ('done', 'cancelled') and
                task.deadline and
                task.deadline < today
            )

    def action_start(self):
        """Start working on the task"""
        self.ensure_one()
        if self.state != 'pending':
            raise UserError('Can only start a pending task.')
        self.state = 'in_progress'
        self.message_post(body=f'Task started by {self.env.user.name}.')
        return True

    def action_mark_blocked(self):
        """Mark task as blocked"""
        self.ensure_one()
        self.state = 'blocked'
        self.message_post(body='Task marked as blocked.')
        return True

    def action_submit_review(self):
        """Submit task for review by accountable person"""
        self.ensure_one()
        if self.state not in ('in_progress', 'blocked'):
            raise UserError('Can only submit in-progress or blocked tasks for review.')

        self.state = 'review'

        # Notify accountable person
        if self.raci_accountable_id:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=self.raci_accountable_id.id,
                summary=f'Review required: {self.name}'
            )

        self.message_post(body='Task submitted for review.')
        return True

    def action_approve(self):
        """Approve and complete the task"""
        self.ensure_one()
        if self.state != 'review':
            raise UserError('Can only approve tasks under review.')

        # Check if user is accountable
        if self.raci_accountable_id and self.env.user != self.raci_accountable_id:
            if not self.env.user.has_group('ipai_month_end.group_month_end_manager'):
                raise UserError('Only the accountable person or a manager can approve.')

        self.write({
            'state': 'done',
            'completed_date': fields.Datetime.now(),
            'completed_by_id': self.env.user.id,
        })

        # Clear activities
        self.activity_ids.unlink()

        self.message_post(body=f'Task approved and completed by {self.env.user.name}.')
        return True

    def action_reject(self):
        """Reject and send back for rework"""
        self.ensure_one()
        if self.state != 'review':
            raise UserError('Can only reject tasks under review.')

        self.state = 'in_progress'

        # Notify responsible person
        if self.raci_responsible_id:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=self.raci_responsible_id.id,
                summary=f'Rework required: {self.name}'
            )

        self.message_post(body='Task rejected - requires rework.')
        return True

    def action_cancel(self):
        """Cancel the task"""
        self.ensure_one()
        if self.state == 'done':
            raise UserError('Cannot cancel completed tasks.')
        self.state = 'cancelled'
        self.message_post(body='Task cancelled.')
        return True


class MonthEndTaskTemplate(models.Model):
    """Template for recurring month-end tasks"""
    _name = 'ipai.month.end.task.template'
    _description = 'Month-End Task Template'
    _order = 'day_offset, scheduled_time, sequence'

    name = fields.Char(
        string='Task Name',
        required=True
    )
    description = fields.Html(
        string='Description'
    )
    checklist_id = fields.Many2one(
        'ipai.month.end.checklist',
        string='Checklist',
        required=True,
        ondelete='cascade'
    )

    # Scheduling
    day_offset = fields.Integer(
        string='Day Offset',
        required=True,
        default=0,
        help='Days from close start (0 = Day 1, 1 = Day 2, etc.)'
    )
    scheduled_time = fields.Char(
        string='Scheduled Time',
        help='e.g., 08:00'
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )

    # Default assignment
    default_assignee_id = fields.Many2one(
        'res.users',
        string='Default Assignee'
    )
    raci_responsible_id = fields.Many2one(
        'res.users',
        string='Default Responsible'
    )
    raci_accountable_id = fields.Many2one(
        'res.users',
        string='Default Accountable'
    )

    # Properties
    is_mandatory = fields.Boolean(
        string='Mandatory',
        default=True
    )
    task_category = fields.Selection([
        ('payroll', 'Payroll'),
        ('vat', 'VAT/Tax'),
        ('accruals', 'Accruals'),
        ('liquidations', 'Liquidations'),
        ('wip', 'WIP Management'),
        ('treasury', 'Treasury/FX'),
        ('reconciliation', 'Reconciliation'),
        ('reporting', 'Reporting'),
        ('review', 'Review/Approval'),
        ('filing', 'Filing/Compliance'),
        ('other', 'Other'),
    ], string='Category', default='other')
