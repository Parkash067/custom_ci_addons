#-*- coding:utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011 OpenERP SA (<http://openerp.com>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields,osv
import time

class supplier_ledger(osv.osv_memory):
    _name='supplier.ledger'

    _columns = {
        'date_from' : fields.date('From Date', required=True),
        'date_to' : fields.date('To Date', required=True),
        'partner_id': fields.many2one('res.partner', 'Supplier Name', required=True, domain=[('supplier','=','True')]),
        }

    _defaults = {
        'date_from': lambda *a: time.strftime('%Y-%m-%d'),
        'date_to': lambda *a: time.strftime('%Y-%m-%d')
    }

    def start_report(self, cr, uid, ids, data, context=None):
        for wiz_obj in self.read(cr,uid,ids):
            if 'form' not in data:
                data['form'] = {}

#            data['form'] = {}
            data['form']['partner_id']   = wiz_obj['partner_id']
            data['form']['date_from']    = wiz_obj['date_from'] 
            data['form']['date_to']      = wiz_obj['date_to']

            return {
                        'type': 'ir.actions.report.xml',
                        'report_name': 'supplier_ledger',
                        'datas': data,
#			'nodestroy': True
                }

supplier_ledger()
