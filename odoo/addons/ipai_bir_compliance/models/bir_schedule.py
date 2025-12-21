# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date
from dateutil.relativedelta import relativedelta


class BIRFilingSchedule(models.Model):
    """BIR Filing Schedule Generator"""
    _name = 'ipai.bir.filing.schedule'
    _description = 'BIR Filing Schedule'
    _order = 'year desc, name'

    name = fields.Char(
        string='Schedule Name',
        required=True
    )
    year = fields.Integer(
        string='Year',
        required=True,
        default=lambda self: date.today().year
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )

    # Forms to include
    form_ids = fields.Many2many(
        'ipai.bir.form',
        'bir_schedule_form_rel',
        'schedule_id',
        'form_id',
        string='BIR Forms'
    )

    # Generated filings
    filing_ids = fields.One2many(
        'ipai.bir.filing',
        'schedule_id',
        string='Generated Filings'
    )

    # Company
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    # Statistics
    filing_count = fields.Integer(
        string='Filing Count',
        compute='_compute_filing_count'
    )
    completed_count = fields.Integer(
        string='Completed',
        compute='_compute_filing_count'
    )
    pending_count = fields.Integer(
        string='Pending',
        compute='_compute_filing_count'
    )

    @api.depends('filing_ids', 'filing_ids.state')
    def _compute_filing_count(self):
        for schedule in self:
            filings = schedule.filing_ids
            schedule.filing_count = len(filings)
            schedule.completed_count = len(filings.filtered(lambda f: f.state == 'filed'))
            schedule.pending_count = len(filings.filtered(lambda f: f.state not in ('filed', 'cancelled')))

    def action_generate_filings(self):
        """Generate filing records for the year"""
        self.ensure_one()
        Filing = self.env['ipai.bir.filing']

        for form in self.form_ids:
            if form.frequency == 'monthly':
                for month in range(1, 13):
                    # Calculate due date
                    period_end = date(self.year, month, 1) + relativedelta(months=1, days=-1)
                    due_date = date(self.year, month, 1) + relativedelta(
                        months=form.due_month_offset,
                        day=form.due_day
                    )

                    # Check if filing already exists
                    existing = Filing.search([
                        ('form_id', '=', form.id),
                        ('period_year', '=', self.year),
                        ('period_month', '=', str(month)),
                        ('company_id', '=', self.company_id.id),
                    ], limit=1)

                    if not existing:
                        Filing.create({
                            'form_id': form.id,
                            'period_year': self.year,
                            'period_month': str(month),
                            'due_date': due_date,
                            'schedule_id': self.id,
                            'company_id': self.company_id.id,
                        })

            elif form.frequency == 'quarterly':
                for quarter in range(1, 5):
                    end_month = quarter * 3
                    due_date = date(self.year, end_month, 1) + relativedelta(
                        months=form.due_month_offset,
                        day=form.due_day
                    )

                    existing = Filing.search([
                        ('form_id', '=', form.id),
                        ('period_year', '=', self.year),
                        ('period_quarter', '=', str(quarter)),
                        ('company_id', '=', self.company_id.id),
                    ], limit=1)

                    if not existing:
                        Filing.create({
                            'form_id': form.id,
                            'period_year': self.year,
                            'period_quarter': str(quarter),
                            'due_date': due_date,
                            'schedule_id': self.id,
                            'company_id': self.company_id.id,
                        })

            elif form.frequency == 'annual':
                due_date = date(self.year + 1, form.due_month_offset, form.due_day)

                existing = Filing.search([
                    ('form_id', '=', form.id),
                    ('period_year', '=', self.year),
                    ('company_id', '=', self.company_id.id),
                ], limit=1)

                if not existing:
                    Filing.create({
                        'form_id': form.id,
                        'period_year': self.year,
                        'due_date': due_date,
                        'schedule_id': self.id,
                        'company_id': self.company_id.id,
                    })

        return {
            'type': 'ir.actions.act_window',
            'name': 'Generated Filings',
            'res_model': 'ipai.bir.filing',
            'view_mode': 'tree,form',
            'domain': [('schedule_id', '=', self.id)],
        }

    def action_view_filings(self):
        """View generated filings"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Filings',
            'res_model': 'ipai.bir.filing',
            'view_mode': 'tree,form',
            'domain': [('schedule_id', '=', self.id)],
        }


# Add schedule reference to filing
class BIRFilingScheduleRef(models.Model):
    _inherit = 'ipai.bir.filing'

    schedule_id = fields.Many2one(
        'ipai.bir.filing.schedule',
        string='Schedule',
        ondelete='set null'
    )
