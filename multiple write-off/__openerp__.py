# -*- coding: utf-8 -*-
{
    'name': "Multiple Write-Off",

    'summary': """Write-Off customer payment into multiple account heads""",

    'description': """
        This module provides you facility to write-off customer payment into more than one account head.
        Add simple check box  on customer payment option mark this and select Reconcile Payment Balance to write-off into multiple account heads
    """,

    'author': "Parkash Kumar",
    'website': "http://pk067.herokuapp.com",

    'category': 'Accounts',
    'version': '0.1',
    'price': 100.00,
    'currency': 'EUR',

    # any module necessary for this one to work correctly
    'depends': ['base','account_accountant'],

    # always loaded
    'data': [
        'write_off_view.xml',
        'payment_registration_view.xml'
    ],

}