# -*- coding: utf-8 -*-
#################################################################################
#
#    Develop By Muhammad Faizan, Karachi, Pakistan (+923322676365)
#
#################################################################################

from openerp.addons import jasper_reports
from openerp.tools.translate import _
from openerp import pooler
from dateutil.rrule import rrule, MONTHLY
from dateutil.relativedelta import relativedelta
from datetime import datetime
from openerp.osv import fields,osv
import string

#--------------DELIVERY ORDER-----------------#

def delivery_order(cr, uid, ids, data, context):

    pool = pooler.get_pool(cr.dbname)
    s_id = pool.get('stock.picking').browse(cr, uid, ids[0], context=context).id

    return {
	'parameters':{
			'x': s_id

		},
	    }

jasper_reports.report_jasper('report.delivery_order','stock.picking',parser=delivery_order)


#--------------CERTIFICATE PRINT-----------------#

def certificate_print(cr, uid, ids, data, context):

    pool = pooler.get_pool(cr.dbname)
    s_id = pool.get('stock.production.lot').browse(cr, uid, ids[0],context=context).id

    return {
	'parameters':{
			'x': s_id,
		},
	    }

# print 'id:' s_id

jasper_reports.report_jasper('report.certificate','stock.production.lot',parser=certificate_print)


#-------- Customer Ledger-------#

def customer_ledger(cr, uid, ids, data, context):
    
    date_from  = data['form']['date_from']
    date_to    = data['form']['date_to']
    part_id = data['form']['partner_id']
    pool = pooler.get_pool(cr.dbname)
#    z          = ''
    if part_id:
        partner_id = part_id[0]
        partner_id = int(partner_id)


    return {
        'parameters': {    
            'from_date' : date_from,
            'to_date'   : date_to,
            'partner_id': partner_id
#            'x'         : z 
        },
   }

jasper_reports.report_jasper('report.customer_ledger', 'account.move.line', parser=customer_ledger)
jasper_reports.report_jasper('report.subreport_aging', 'account.move.line', parser=customer_ledger)


#-------- Supplier Ledger-------#

def supplier_ledger(cr, uid, ids, data, context):
    
    date_from  = data['form']['date_from']
    date_to    = data['form']['date_to']
    part_id = data['form']['partner_id']
    pool = pooler.get_pool(cr.dbname)
#    z          = ''
    if part_id:
        partner_id = part_id[0]
        partner_id = int(partner_id)


    return {
        'parameters': {    
            'from_date' : date_from,
            'to_date'   : date_to,
            'partner_id': partner_id
#            'x'         : z 
        },
   }

jasper_reports.report_jasper('report.supplier_ledger', 'account.move.line', parser=supplier_ledger)
jasper_reports.report_jasper('report.subreport_aging_1', 'account.move.line', parser=supplier_ledger)


#-------- Partner Trial -------#

def partner_trial(cr, uid, ids, data, context):
    
    date_from  = data['form']['date_from']
    date_to    = data['form']['date_to']
    region     = data['form']['region']
    partner    = data['form']['partner']
    pool = pooler.get_pool(cr.dbname)
    z = ''

    if region:
        z1 = ' AND res_partner.region_id = ' + str(region[0])
    else:
        z1 = '' 

    if partner:
        z2 = ' AND res_partner.id = ' + str(partner[0])
    else:
        z2 = '' 

    z = z1 + z2

    return {
        'parameters': {    
            'from_date' : date_from,
            'to_date'   : date_to,
            'x'         : z,
        },
   }

jasper_reports.report_jasper('report.partner_trial', 'account.move.line', parser=partner_trial)


#-------- Aging Report -------#

def aging_report(cr, uid, ids, data, context):
    date_to    = data['form']['date_to']
    date_from  = data['form']['date_from']
    partner    = data['form']['partner']
    region     = data['form']['region']
    pool = pooler.get_pool(cr.dbname)
    z = ''

    if region:
        z1 = ' AND x.region_id = ' + str(region[0])
    else:
        z1 = '' 


    if partner:
        y = str(partner)
        for char in string.punctuation:
                y = y.replace(char, '')
        y = y.replace(' ', ',')
        z6 = ' AND x.id IN ' + '(' + y + ')'
        obj = pool.get('res.partner')
        ids = partner
        res = obj.read(cr, uid, ids, ['name'])
        partner_id = [(r['name']) for r in res]
        partner = ', '.join(partner_id)
    else:
        z6 = ''
        partner = 'All Customers'

    z = str(z6) + z1

    return {
        'parameters': {    
            'date_to' : date_to,
            'date_from' : date_from,
            'partner' : partner,
	    'x' : z,
        },
   }

jasper_reports.report_jasper('report.aging_report', 'account.move.line', parser=aging_report)


#-------- Supplier Aging Report -------#

def aging_report_supplier(cr, uid, ids, data, context):
    date_to    = data['form']['date_to']
    date_from  = data['form']['date_from']
    partner    = data['form']['partner']
    region     = data['form']['region']
    pool = pooler.get_pool(cr.dbname)
    z = ''

    if region:
        z1 = ' AND x.region_id = ' + str(region[0])
    else:
        z1 = '' 


    if partner:
        y = str(partner)
        for char in string.punctuation:
                y = y.replace(char, '')
        y = y.replace(' ', ',')
        z6 = ' AND x.id IN ' + '(' + y + ')'
        obj = pool.get('res.partner')
        ids = partner
        res = obj.read(cr, uid, ids, ['name'])
        partner_id = [(r['name']) for r in res]
        partner = ', '.join(partner_id)
    else:
        z6 = ''
        partner = 'All Suppliers'

    z = str(z6) + z1

    return {
        'parameters': {    
            'date_to' : date_to,
            'date_from' : date_from,
            'partner' : partner,
	    'x' : z,
        },
   }

jasper_reports.report_jasper('report.aging_report_supplier', 'account.move.line', parser=aging_report_supplier)
