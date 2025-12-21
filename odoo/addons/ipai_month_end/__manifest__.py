# -*- coding: utf-8 -*-
{
    'name': 'IPAI Month-End Close',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Automated month-end close management with task tracking and approvals',
    'description': """
IPAI Month-End Close Module
===========================

This module provides comprehensive month-end close management for TBWA/InsightPulse AI:

Features:
---------
* Period close checklists with task assignments
* Automated status tracking and escalation
* Integration with approval workflows
* Real-time dashboard updates
* Task dependencies and sequencing
* Multi-user role-based assignments (RACI)
* Audit trail for all close activities

Month-End Process Support:
--------------------------
* Payroll processing coordination
* VAT data compilation
* Accruals and adjustments
* CA liquidations tracking
* WIP management
* Treasury & FX revaluation
* Regional reporting
* Trial balance review and approval
* GL period close
    """,
    'author': 'InsightPulse AI',
    'website': 'https://insightpulseai.net',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'account',
        'hr',
        'ipai_approval_workflow',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/month_end_security.xml',
        'data/month_end_tasks.xml',
        'data/month_end_sequence.xml',
        'views/month_end_views.xml',
        'views/month_end_task_views.xml',
        'views/menu_views.xml',
        'wizards/create_period_wizard.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
