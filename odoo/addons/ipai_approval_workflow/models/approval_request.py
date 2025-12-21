# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta


class ApprovalRequest(models.Model):
    """Approval Request Management"""
    _name = 'ipai.approval.request'
    _description = 'Approval Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(
        string='Reference',
        required=True,
        readonly=True,
        default=lambda self: self.env['ir.sequence'].next_by_code('ipai.approval.request'),
        tracking=True
    )
    subject = fields.Char(
        string='Subject',
        required=True,
        tracking=True
    )
    description = fields.Html(
        string='Description'
    )

    # Source document reference
    res_model = fields.Char(
        string='Related Document Model',
        index=True
    )
    res_id = fields.Integer(
        string='Related Document ID',
        index=True
    )

    # Rule and stages
    rule_id = fields.Many2one(
        'ipai.approval.rule',
        string='Approval Rule',
        required=True,
        tracking=True
    )
    current_stage_id = fields.Many2one(
        'ipai.approval.stage',
        string='Current Stage',
        tracking=True
    )
    stage_ids = fields.One2many(
        'ipai.approval.stage.instance',
        'request_id',
        string='Approval Stages'
    )

    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    # Requester
    requester_id = fields.Many2one(
        'res.users',
        string='Requested By',
        default=lambda self: self.env.user,
        tracking=True
    )
    request_date = fields.Datetime(
        string='Request Date',
        default=fields.Datetime.now
    )

    # Deadline and escalation
    deadline = fields.Datetime(
        string='Approval Deadline',
        tracking=True
    )
    escalation_date = fields.Datetime(
        string='Escalation Date',
        help='Date when request will be escalated if not approved'
    )
    is_escalated = fields.Boolean(
        string='Escalated',
        default=False,
        tracking=True
    )

    # Completion
    completed_date = fields.Datetime(
        string='Completed Date'
    )
    final_approver_id = fields.Many2one(
        'res.users',
        string='Final Approver'
    )

    # Company
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )

    # Priority
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'Low'),
        ('2', 'High'),
        ('3', 'Urgent'),
    ], string='Priority', default='0', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('ipai.approval.request') or '/'
        return super().create(vals_list)

    def action_submit(self):
        """Submit request for approval"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError('Can only submit draft requests.')

        if not self.rule_id:
            raise UserError('Please select an approval rule.')

        # Generate stage instances from rule
        self._generate_stages()

        # Set first stage as current
        first_stage = self.stage_ids.sorted('sequence')[0] if self.stage_ids else False
        if first_stage:
            first_stage.state = 'pending'
            self.current_stage_id = first_stage.stage_id

        # Calculate deadline if rule has one
        if self.rule_id.approval_timeout_hours:
            self.deadline = fields.Datetime.now() + timedelta(hours=self.rule_id.approval_timeout_hours)
            self.escalation_date = self.deadline

        self.state = 'pending'
        self.message_post(body='Approval request submitted.')

        # Notify approvers
        self._notify_current_approvers()

        return True

    def action_approve(self):
        """Approve current stage"""
        self.ensure_one()
        if self.state != 'pending':
            raise UserError('Can only approve pending requests.')

        current_instance = self._get_current_stage_instance()
        if not current_instance:
            raise UserError('No pending stage found.')

        # Check if user can approve
        if not self._can_user_approve(current_instance):
            raise UserError('You are not authorized to approve this stage.')

        # Mark stage as approved
        current_instance.write({
            'state': 'approved',
            'approved_by_id': self.env.user.id,
            'approval_date': fields.Datetime.now(),
        })

        self.message_post(body=f'Stage "{current_instance.stage_id.name}" approved by {self.env.user.name}.')

        # Move to next stage or complete
        next_stage = self._get_next_pending_stage()
        if next_stage:
            next_stage.state = 'pending'
            self.current_stage_id = next_stage.stage_id
            self._notify_current_approvers()
        else:
            # All stages approved
            self.write({
                'state': 'approved',
                'completed_date': fields.Datetime.now(),
                'final_approver_id': self.env.user.id,
            })
            self._notify_completion('approved')

        return True

    def action_reject(self):
        """Reject the request"""
        self.ensure_one()
        if self.state != 'pending':
            raise UserError('Can only reject pending requests.')

        current_instance = self._get_current_stage_instance()
        if current_instance:
            if not self._can_user_approve(current_instance):
                raise UserError('You are not authorized to reject this stage.')

            current_instance.write({
                'state': 'rejected',
                'approved_by_id': self.env.user.id,
                'approval_date': fields.Datetime.now(),
            })

        self.write({
            'state': 'rejected',
            'completed_date': fields.Datetime.now(),
        })

        self.message_post(body=f'Request rejected by {self.env.user.name}.')
        self._notify_completion('rejected')

        return True

    def action_cancel(self):
        """Cancel the request"""
        self.ensure_one()
        if self.state in ('approved', 'rejected'):
            raise UserError('Cannot cancel completed requests.')

        self.state = 'cancelled'
        self.message_post(body='Request cancelled.')
        return True

    def action_reset_to_draft(self):
        """Reset to draft for modification"""
        self.ensure_one()
        if self.state not in ('rejected', 'cancelled'):
            raise UserError('Can only reset rejected or cancelled requests.')

        # Clear stages
        self.stage_ids.unlink()
        self.current_stage_id = False

        self.state = 'draft'
        self.message_post(body='Request reset to draft.')
        return True

    def _generate_stages(self):
        """Generate stage instances from rule template"""
        self.ensure_one()
        StageInstance = self.env['ipai.approval.stage.instance']

        for stage in self.rule_id.stage_ids.sorted('sequence'):
            StageInstance.create({
                'request_id': self.id,
                'stage_id': stage.id,
                'sequence': stage.sequence,
                'state': 'waiting',
            })

    def _get_current_stage_instance(self):
        """Get the current pending stage instance"""
        return self.stage_ids.filtered(lambda s: s.state == 'pending')[:1]

    def _get_next_pending_stage(self):
        """Get the next waiting stage"""
        return self.stage_ids.filtered(lambda s: s.state == 'waiting').sorted('sequence')[:1]

    def _can_user_approve(self, stage_instance):
        """Check if current user can approve the stage"""
        stage = stage_instance.stage_id
        user = self.env.user

        # Check if user is in approver list
        if user in stage.approver_ids:
            return True

        # Check if user is in approver group
        if stage.approver_group_id and user in stage.approver_group_id.users:
            return True

        # Check if user is manager
        if user.has_group('ipai_approval_workflow.group_approval_manager'):
            return True

        return False

    def _notify_current_approvers(self):
        """Send notifications to current stage approvers"""
        current_instance = self._get_current_stage_instance()
        if not current_instance:
            return

        stage = current_instance.stage_id
        approvers = stage.approver_ids

        if stage.approver_group_id:
            approvers |= stage.approver_group_id.users

        for approver in approvers:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=approver.id,
                summary=f'Approval required: {self.subject}'
            )

    def _notify_completion(self, status):
        """Notify requester of completion"""
        # Clear activities
        self.activity_ids.unlink()

        # Notify requester
        body = f'Your approval request "{self.subject}" has been {status}.'
        self.message_post(
            body=body,
            partner_ids=[self.requester_id.partner_id.id]
        )

    @api.model
    def _cron_check_escalations(self):
        """Cron job to check and escalate overdue requests"""
        now = fields.Datetime.now()
        overdue = self.search([
            ('state', '=', 'pending'),
            ('escalation_date', '<=', now),
            ('is_escalated', '=', False),
        ])

        for request in overdue:
            request._escalate()

    def _escalate(self):
        """Escalate overdue request"""
        self.ensure_one()
        self.is_escalated = True

        # Notify managers
        managers = self.env.ref('ipai_approval_workflow.group_approval_manager').users
        for manager in managers:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=manager.id,
                summary=f'ESCALATED: {self.subject}'
            )

        self.message_post(
            body='Request has been escalated due to timeout.',
            message_type='notification'
        )


class ApprovalStageInstance(models.Model):
    """Instance of approval stage for a specific request"""
    _name = 'ipai.approval.stage.instance'
    _description = 'Approval Stage Instance'
    _order = 'sequence'

    request_id = fields.Many2one(
        'ipai.approval.request',
        string='Request',
        required=True,
        ondelete='cascade'
    )
    stage_id = fields.Many2one(
        'ipai.approval.stage',
        string='Stage',
        required=True
    )
    sequence = fields.Integer(
        string='Sequence'
    )
    state = fields.Selection([
        ('waiting', 'Waiting'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('skipped', 'Skipped'),
    ], string='Status', default='waiting')

    approved_by_id = fields.Many2one(
        'res.users',
        string='Approved/Rejected By'
    )
    approval_date = fields.Datetime(
        string='Approval Date'
    )
    notes = fields.Text(
        string='Notes'
    )
