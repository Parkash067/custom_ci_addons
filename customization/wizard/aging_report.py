# -*- coding: utf-8 -*-
##############################################################################
#    
#    Copyright (C) 2011 Agile Business Group sagl (<http://www.agilebg.com>)
#    Copyright (C) 2011 Domsense srl (<http://www.domsense.com>)
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields,osv
from openerp.tools.translate import _
import time

class aging_report(osv.osv_memory):
    _name = "aging.report"
    _columns = {
        'date_to': fields.date('To Date', required=True),
	'date_from': fields.date('From Date', required=True),
        'region': fields.many2one('res.region','Region'),
        'partner_id': fields.many2many('res.partner','aging_parnter_rel', 'partner_id', 'report_id', 'Customer Name', domain=[('customer','=','True')]),
    }
    
    _defaults = {
        'date_to': lambda *a: time.strftime('%Y-%m-%d'),
        'date_from': lambda *a: time.strftime('%Y-%m-%d')
    }

    def start_report(self, cr, uid, ids, data, context=None):
        for wiz_obj in self.read(cr,uid,ids):
            if 'form' not in data:
                data['form'] = {}

            data['form'] = {}
            data['form']['date_to'] = wiz_obj['date_to']
            data['form']['date_from'] = wiz_obj['date_from']
            data['form']['partner'] = wiz_obj['partner_id']
            data['form']['region'] = wiz_obj['region']

            return {
                    'type': 'ir.actions.report.xml',
                    'report_name': 'aging_report',
                    'datas': data,
                    'nodestroy': True
                }
                

aging_report()
