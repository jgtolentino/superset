# -*- coding: utf-8 -*-
{
    'name': 'IPAI BIR Compliance',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Localizations',
    'summary': 'Philippine BIR tax compliance and filing management',
    'description': """
IPAI BIR Compliance Module
==========================

This module provides comprehensive BIR (Bureau of Internal Revenue) compliance
management for TBWA/InsightPulse AI Philippines operations:

Supported BIR Forms:
--------------------
* BIR 1601-C - Monthly Remittance of Creditable Income Taxes Withheld
* BIR 2550M - Monthly VAT Declaration
* BIR 2550Q - Quarterly VAT Return
* BIR 1701Q - Quarterly Income Tax Return
* BIR 0619E - Monthly Remittance of Expanded Withholding Tax
* BIR 2307 - Certificate of Creditable Tax Withheld at Source

Features:
---------
* Tax period management with deadlines
* Automatic filing schedule generation
* Form preparation and validation
* Approval workflow integration
* Filing status tracking
* Compliance dashboard
* Due date alerts and reminders
* Audit trail for all filings
* BIR form generation (PDF/DAT)
    """,
    'author': 'InsightPulse AI',
    'website': 'https://insightpulseai.net',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'account',
        'ipai_approval_workflow',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/bir_security.xml',
        'data/bir_form_data.xml',
        'data/bir_schedule_data.xml',
        'views/bir_filing_views.xml',
        'views/bir_form_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
