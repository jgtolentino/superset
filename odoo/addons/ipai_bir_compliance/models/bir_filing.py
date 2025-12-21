# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import date
from dateutil.relativedelta import relativedelta


class BIRFiling(models.Model):
    """BIR Filing Record"""
    _name = 'ipai.bir.filing'
    _description = 'BIR Filing'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'due_date desc, form_id'

    name = fields.Char(
        string='Reference',
        required=True,
        readonly=True,
        default='/',
        tracking=True
    )

    # Form and period
    form_id = fields.Many2one(
        'ipai.bir.form',
        string='BIR Form',
        required=True,
        tracking=True
    )
    form_code = fields.Char(
        related='form_id.code',
        store=True
    )
    period_year = fields.Integer(
        string='Year',
        required=True,
        default=lambda self: date.today().year,
        tracking=True
    )
    period_month = fields.Selection([
        ('1', 'January'), ('2', 'February'), ('3', 'March'),
        ('4', 'April'), ('5', 'May'), ('6', 'June'),
        ('7', 'July'), ('8', 'August'), ('9', 'September'),
        ('10', 'October'), ('11', 'November'), ('12', 'December'),
    ], string='Month', tracking=True)
    period_quarter = fields.Selection([
        ('1', 'Q1'), ('2', 'Q2'), ('3', 'Q3'), ('4', 'Q4'),
    ], string='Quarter', tracking=True)

    # Dates
    period_start = fields.Date(
        string='Period Start',
        compute='_compute_period_dates',
        store=True
    )
    period_end = fields.Date(
        string='Period End',
        compute='_compute_period_dates',
        store=True
    )
    due_date = fields.Date(
        string='Due Date',
        required=True,
        tracking=True
    )
    filing_date = fields.Date(
        string='Filing Date',
        tracking=True
    )

    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('preparing', 'Preparing'),
        ('review', 'Under Review'),
        ('approved', 'Approved'),
        ('filed', 'Filed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    # Amounts
    tax_base = fields.Monetary(
        string='Tax Base',
        currency_field='currency_id',
        tracking=True
    )
    tax_due = fields.Monetary(
        string='Tax Due',
        currency_field='currency_id',
        tracking=True
    )
    tax_credits = fields.Monetary(
        string='Tax Credits',
        currency_field='currency_id'
    )
    tax_payable = fields.Monetary(
        string='Tax Payable',
        currency_field='currency_id',
        compute='_compute_tax_payable',
        store=True
    )
    penalty = fields.Monetary(
        string='Penalty',
        currency_field='currency_id'
    )
    total_amount = fields.Monetary(
        string='Total Amount Due',
        currency_field='currency_id',
        compute='_compute_total_amount',
        store=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )

    # Filing details
    confirmation_number = fields.Char(
        string='Confirmation Number',
        tracking=True
    )
    transaction_code = fields.Char(
        string='Transaction Code'
    )
    payment_reference = fields.Char(
        string='Payment Reference'
    )

    # Assignment
    preparer_id = fields.Many2one(
        'res.users',
        string='Preparer',
        default=lambda self: self.env.user,
        tracking=True
    )
    reviewer_id = fields.Many2one(
        'res.users',
        string='Reviewer',
        tracking=True
    )
    approver_id = fields.Many2one(
        'res.users',
        string='Approver',
        tracking=True
    )

    # Approval integration
    approval_request_id = fields.Many2one(
        'ipai.approval.request',
        string='Approval Request'
    )

    # Attachments tracking
    attachment_count = fields.Integer(
        string='Attachments',
        compute='_compute_attachment_count'
    )

    # Company
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    )

    # Notes
    notes = fields.Html(
        string='Notes'
    )

    # Computed flags
    is_overdue = fields.Boolean(
        string='Overdue',
        compute='_compute_is_overdue',
        store=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                form = self.env['ipai.bir.form'].browse(vals.get('form_id'))
                prefix = f"BIR-{form.code}-" if form else "BIR-"
                vals['name'] = self.env['ir.sequence'].next_by_code('ipai.bir.filing') or '/'
                if vals['name'] == '/':
                    vals['name'] = f"{prefix}{vals.get('period_year', '')}"
        return super().create(vals_list)

    @api.depends('period_year', 'period_month', 'period_quarter', 'form_id.frequency')
    def _compute_period_dates(self):
        for filing in self:
            if not filing.period_year:
                filing.period_start = False
                filing.period_end = False
                continue

            if filing.form_id.frequency == 'monthly' and filing.period_month:
                month = int(filing.period_month)
                filing.period_start = date(filing.period_year, month, 1)
                filing.period_end = date(filing.period_year, month, 1) + relativedelta(months=1, days=-1)
            elif filing.form_id.frequency == 'quarterly' and filing.period_quarter:
                quarter = int(filing.period_quarter)
                start_month = (quarter - 1) * 3 + 1
                filing.period_start = date(filing.period_year, start_month, 1)
                filing.period_end = date(filing.period_year, start_month, 1) + relativedelta(months=3, days=-1)
            elif filing.form_id.frequency == 'annual':
                filing.period_start = date(filing.period_year, 1, 1)
                filing.period_end = date(filing.period_year, 12, 31)
            else:
                filing.period_start = False
                filing.period_end = False

    @api.depends('tax_due', 'tax_credits')
    def _compute_tax_payable(self):
        for filing in self:
            filing.tax_payable = filing.tax_due - filing.tax_credits

    @api.depends('tax_payable', 'penalty')
    def _compute_total_amount(self):
        for filing in self:
            filing.total_amount = filing.tax_payable + filing.penalty

    @api.depends('due_date', 'state')
    def _compute_is_overdue(self):
        today = fields.Date.today()
        for filing in self:
            filing.is_overdue = (
                filing.state not in ('filed', 'cancelled') and
                filing.due_date and
                filing.due_date < today
            )

    def _compute_attachment_count(self):
        Attachment = self.env['ir.attachment']
        for filing in self:
            filing.attachment_count = Attachment.search_count([
                ('res_model', '=', self._name),
                ('res_id', '=', filing.id),
            ])

    def action_prepare(self):
        """Start preparing the filing"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError('Can only prepare draft filings.')
        self.state = 'preparing'
        self.message_post(body='Filing preparation started.')
        return True

    def action_submit_review(self):
        """Submit for review"""
        self.ensure_one()
        if self.state != 'preparing':
            raise UserError('Can only submit filings in preparation.')

        # Create approval request if form has approval rule
        if self.form_id.approval_rule_id:
            approval = self.env['ipai.approval.request'].create({
                'subject': f'{self.form_id.code} Filing - {self.name}',
                'description': f'BIR {self.form_id.code} filing for period ending {self.period_end}',
                'rule_id': self.form_id.approval_rule_id.id,
                'res_model': self._name,
                'res_id': self.id,
            })
            approval.action_submit()
            self.approval_request_id = approval.id

        self.state = 'review'
        self.message_post(body='Filing submitted for review.')
        return True

    def action_approve(self):
        """Approve the filing"""
        self.ensure_one()
        if self.state != 'review':
            raise UserError('Can only approve filings under review.')

        self.write({
            'state': 'approved',
            'approver_id': self.env.user.id,
        })
        self.message_post(body=f'Filing approved by {self.env.user.name}.')
        return True

    def action_file(self):
        """Mark as filed with BIR"""
        self.ensure_one()
        if self.state != 'approved':
            raise UserError('Can only file approved filings.')

        self.write({
            'state': 'filed',
            'filing_date': fields.Date.today(),
        })
        self.message_post(body='Filing submitted to BIR.')
        return True

    def action_cancel(self):
        """Cancel the filing"""
        self.ensure_one()
        if self.state == 'filed':
            raise UserError('Cannot cancel filed submissions.')
        self.state = 'cancelled'
        self.message_post(body='Filing cancelled.')
        return True

    def action_reset_draft(self):
        """Reset to draft"""
        self.ensure_one()
        if self.state == 'filed':
            raise UserError('Cannot reset filed submissions.')
        self.state = 'draft'
        self.message_post(body='Filing reset to draft.')
        return True

    def action_view_attachments(self):
        """View attachments"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Attachments',
            'res_model': 'ir.attachment',
            'view_mode': 'tree,form',
            'domain': [('res_model', '=', self._name), ('res_id', '=', self.id)],
            'context': {'default_res_model': self._name, 'default_res_id': self.id},
        }

    @api.model
    def _cron_check_due_dates(self):
        """Cron job to send reminders for upcoming due dates"""
        today = fields.Date.today()
        reminder_date = today + relativedelta(days=3)

        upcoming = self.search([
            ('state', 'in', ('draft', 'preparing', 'review')),
            ('due_date', '<=', reminder_date),
            ('due_date', '>=', today),
        ])

        for filing in upcoming:
            filing.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=filing.preparer_id.id or self.env.user.id,
                summary=f'BIR {filing.form_code} due on {filing.due_date}',
                date_deadline=filing.due_date,
            )
