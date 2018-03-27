from openerp import models,fields,api
from openerp.osv import fields,osv
from datetime import date, timedelta,datetime
import xlwt
import StringIO
import base64


class WizardReports(osv.TransientModel):
    _name = 'wiz.reports'
    _description = 'PDF Reports for showing all disconnection,reconnection'

    _columns = {
        'type': fields.selection([('Collection Report', 'Collection Report'),
                                  ('Individual Aging', 'Individual Aging'),
                                  ('Sales Register', 'Sales Register')], 'Report Type', store=True),
        'date_from': fields.date('Start Date'),
        'date_to': fields.date('End Date'),
        'partner_id': fields.many2one('res.partner', 'Customer'),
        'company_id': fields.many2one('res.company', 'Company'),
        'multiple_customers': fields.boolean('Multiple Customer'),

    }

    _defaults = {
        'date_from': lambda *a: datetime.now().strftime('%Y-%m-%d'),
        'date_to': lambda *a: datetime.now().strftime('%Y-%m-%d'),
        'multiple_customers': False
    }



    def check_dates(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids, context=context)[0]
        if wizard.date_from:
            if wizard.date_from > wizard.date_to:
                return False
            if wizard.date_to > fields.date.today():
                return False
        return True

    _constraints = [(check_dates,
                     'Error: Invalid Dates\nDate From must be less than Date To\nDate To must not be greater than todays date.',
                     ['date_from', 'date_to']), ]

    def report_data(self, data,account_head):
        res = {}
        for rec in data:
            partner_id = self.env['res.partner'].search([['id', '=', rec['partner_id']],])
            res = {
                'customer': partner_id.name,
                'account_head': account_head,
                'entry': rec['ref'],
                'particulars': rec['name'],
                'date': rec['date'],
                'amount': rec['debit'],
            }
        return res

    def collection_report(self):
        res = []
        account_ids = self.env['account.account'].search([['type', '=', 'liquidity'],['company_id', '=', self.company_id.id]])
        for id in account_ids:
            self.env.cr.execute("select account_move_line.ref,account_move_line.partner_id,account_move_line.debit,account_move_line.date,account_move_line.account_id,account_move_line.name from account_move_line where account_move_line.account_id="+str(id.id)+" and "+"account_move_line.date between'"+str(self.date_from)+"'"+" and '"+str(self.date_to)+"'")
            data = self.env.cr.dictfetchall()
            if len(data)>0:
                res.append(self.report_data(data,id.name))
        return res

    def individual_aging_report(self):
        data = []
        if self.multiple_customers==False:
            self.env.cr.execute("select account_invoice.number,account_invoice.partner_id,account_invoice.date_invoice,account_invoice.amount_total from account_invoice where account_invoice.date_invoice between'" + str(self.date_from) + "'" + " and '" + str(self.date_to) + "'"+"and state='open'"+"and account_invoice.company_id="+str(self.company_id.id)+"order by account_invoice.date_invoice")
            data = self.env.cr.dictfetchall()
        return data

    def sales_register_report(self):
        self.env.cr.execute(
                "select * from custom_dummy_invoice_line where custom_dummy_invoice_line.date between'" + str(
                    self.date_from) + "'" + " and '" + str(
                    self.date_to) + "'"+"order by account_invoice.date")
        data = self.env.cr.dictfetchall()
        return data

    def print_report(self, cr, uid, ids, data, context=None):
        obj = self.browse(cr, uid, ids[0], context=context)
        if obj.type == 'Collection Report':
            return {
                'type': 'ir.actions.report.xml',
                'name': 'custom_inventory.wiz_collection_report',
                'report_name': 'custom_inventory.wiz_collection_report'
            }
        elif obj.type == 'Individual Aging':
            return {
                'type': 'ir.actions.report.xml',
                'name': 'custom_inventory.wiz_individual_aging_report',
                'report_name': 'custom_inventory.wiz_individual_aging_report'
            }
        elif obj.type == 'Sales Register':
            return {
                'type': 'ir.actions.report.xml',
                'name': 'custom_inventory.wiz_sales_register_report',
                'report_name': 'custom_inventory.wiz_sales_register_report'
            }


