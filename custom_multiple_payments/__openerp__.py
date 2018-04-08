# -*- coding: utf-8 -*-
{
    'name': "Register Multiple Payments",

    'summary': """Show cs number on the Invoice""",

    'description': """
        Register Muliple Payment through Journal Enteries
    """,

    'author': "Team Emotive Labs",
    'website': "www.emotivelabs.ca",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Mutual',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','account_accountant'],

    # always loaded
    'data': [
        'views/account_move_view.xml',
    ],

}