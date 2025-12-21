# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date
from dateutil.relativedelta import relativedelta


class CreatePeriodWizard(models.TransientModel):
    """Wizard for creating month-end close periods"""
    _name = 'ipai.month.end.create.period.wizard'
    _description = 'Create Month-End Period Wizard'

    year = fields.Integer(
        string='Year',
        required=True,
        default=lambda self: date.today().year
    )
    month = fields.Selection([
        ('1', 'January'),
        ('2', 'February'),
        ('3', 'March'),
        ('4', 'April'),
        ('5', 'May'),
        ('6', 'June'),
        ('7', 'July'),
        ('8', 'August'),
        ('9', 'September'),
        ('10', 'October'),
        ('11', 'November'),
        ('12', 'December'),
    ], string='Month', required=True, default=lambda self: str(date.today().month))

    checklist_id = fields.Many2one(
        'ipai.month.end.checklist',
        string='Checklist Template',
        required=True
    )
    close_days = fields.Integer(
        string='Close Duration (Days)',
        default=10,
        help='Number of days for the close process'
    )

    def action_create_period(self):
        """Create the month-end period"""
        self.ensure_one()

        month = int(self.month)
        year = self.year

        # Calculate period dates
        period_start = date(year, month, 1)
        if month == 12:
            period_end = date(year + 1, 1, 1) - relativedelta(days=1)
        else:
            period_end = date(year, month + 1, 1) - relativedelta(days=1)

        # Close starts the day after month ends
        close_start = period_end + relativedelta(days=1)
        close_deadline = close_start + relativedelta(days=self.close_days - 1)

        # Create period
        period = self.env['ipai.month.end.period'].create({
            'name': f"{period_start.strftime('%B %Y')} Close",
            'code': f"{year}-{month:02d}",
            'date_start': period_start,
            'date_end': period_end,
            'close_start_date': close_start,
            'close_deadline': close_deadline,
            'checklist_id': self.checklist_id.id,
            'state': 'pending',
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'ipai.month.end.period',
            'res_id': period.id,
            'view_mode': 'form',
            'target': 'current',
        }
