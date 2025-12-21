# -*- coding: utf-8 -*-
{
    'name': 'IPAI Approval Workflow',
    'version': '17.0.1.0.0',
    'category': 'Productivity',
    'summary': 'Multi-level approval workflow engine with RACI matrix support',
    'description': """
IPAI Approval Workflow Module
=============================

This module provides a comprehensive approval workflow engine for TBWA/InsightPulse AI:

Features:
---------
* Multi-level approval chains
* RACI matrix integration (Responsible, Accountable, Consulted, Informed)
* Configurable approval rules and thresholds
* Automatic escalation on timeout
* Email notifications at each approval stage
* Audit trail for compliance
* Dashboard for pending approvals
* Mobile-friendly approval interface

Workflow Types Supported:
-------------------------
* Month-end close task approvals
* BIR filing approvals
* Payment batch approvals
* Journal entry approvals
* Document approvals
    """,
    'author': 'InsightPulse AI',
    'website': 'https://insightpulseai.net',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/approval_security.xml',
        'data/approval_data.xml',
        'views/approval_views.xml',
        'views/approval_rule_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
