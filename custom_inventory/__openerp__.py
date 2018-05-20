# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Inventory Management',
    'version': '1.0',
    'author':'',
    'summary': 'Inventory, Logistics, Warehousing',
    'description': """
Manage multi-warehouses, multi- and structured stock locations
==============================================================

The warehouse and inventory management is based on a hierarchical location structure, from warehouses to storage bins.
The double entry inventory system allows you to manage customers, vendors as well as manufacturing inventories.

OpenERP has the capacity to manage lots and serial numbers ensuring compliance with the traceability requirements imposed by the majority of industries.

Key Features
------------
* Moves history and planning,
* Minimum stock rules
* Support for barcodes
* Rapid detection of mistakes through double entry system
* Traceability (Serial Numbers, Packages, ...)

Dashboard / Reports for Inventory Management will include:
----------------------------------------------------------
* Incoming Products (Graph)
* Outgoing Products (Graph)
* Procurement in Exception
* Inventory Analysis
* Last Product Inventories
* Moves Analysis
    """,
    'website': 'https://www.odoo.com/page/warehouse',
    'depends': ['base','stock','mrp','sale'],
    'category': 'Inventory Management',
    'sequence': 13,
    'data': [
        'views/finished_raw_products.xml',
        'views/custom_header_po.xml',
        'views/custom_header.xml',
        'views/manufactured_products.xml',
        'views/custom_template.xml',
        'views/post_dated.xml',
        'views/sale_history.xml',
        'views/purchase_order_print.xml',
        'security/certificate_security.xml',
        'security/ir.model.access.csv',
        'views/custom_sale_view.xml',
        'views/po_view.xml',
        'views/custom_stock_move_view.xml',
        'views/custom_stock_transfer_wiz.xml',
        'views/certificate_print.xml',
        'views/delivery_order_print.xml',
        'views/custom_sale_invoice.xml',
        'views/certificate_issuance.xml',
        'views/stock_serial_view.xml',
        'views/sale_letter_summary_remain.xml',
        'views/do_print.xml',
        'views/wiz_view.xml',
        'views/xls_file.xml',
        'views/collection_report.xml',
        'views/wiz_individual_aging_report.xml',
        'views/wiz_mw_progress_report.xml',
        'views/report_menu.xml',
        'views/certificate_view.xml',
        'views/custom_dummy_invoice_view.xml',
        'views/manufacturing_view.xml',
        'views/claim_view.xml',
        'views/debit_note_view.xml',
        'views/serials.xml',
        'views/debit_note_sequence.xml',
        'views/page_setup.xml',
        'views/account_voucher.xml',
        ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
