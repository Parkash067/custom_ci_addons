from openerp import models,fields,api
from openerp.osv import fields,osv
from datetime import date, timedelta,datetime


class WizardReports(osv.TransientModel):
    _name = 'wiz.reports'
    _description = 'PDF Reports for showing all disconnection,reconnection'

    _columns = {
        'date_from': fields.date('Start Date'),
        'date_to': fields.date('End Date'),
        'company_id': fields.many2one('res.company', 'Company', required=True),
    }

    _defaults = {
        'date_from': lambda *a: datetime.now().strftime('%Y-%m-%d'),
        'date_to': lambda *a: datetime.now().strftime('%Y-%m-%d'),
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

    def collection_report_data(self, data,account_head):
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
                res.append(self.collection_report_data(data,id.name))
        return res

    def print_report(self, cr, uid, ids, data, context=None):
        return {
            'type': 'ir.actions.report.xml',
            'name': 'custom_inventory.wiz_report',
            'report_name': 'custom_inventory.wiz_report'
        }


