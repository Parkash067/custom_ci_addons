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
        'type': fields.selection([('Certificate Issuance With Invoice Date Wise', 'Certificate Issuance With Invoice Date Wise'),
                                  ('Certificate Issuance With Invoice Dealer Wise', 'Certificate Issuance With Invoice Dealer Wise'),
                                  ('Sale Letter Summary (Remain)', 'Sale Letter Summary (Remain)'),
                                  ], 'Report Type'),
        'partner_id': fields.many2one('res.partner',string='Dealer'),
        'date_from': fields.date('Start Date'),
        'date_to': fields.date('End Date'),
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

    def certificate_issuance(self):
      self.env.cr.execute("""
      select csm.id,csm.issuance_date,csm.engine_number,csm.chassis_number,csm.dealer_name,
      csm.do_number,csm.do_date,csm.inv_date,csm.inv_num_sara,csm.inv_num_abc
      from custom_stock_move as csm where csm.issuance_date is not null and (csm.issuance_date between '%s' and '%s') order by csm.issuance_date asc,csm.dealer_name asc"""%(self.date_from,self.date_to))

      result = self.env.cr.dictfetchall()
      return result

    def certificate_issuance_dealer_wise(self):
        self.env.cr.execute("""
         select csm.id,csm.issuance_date,csm.engine_number,csm.chassis_number,csm.dealer_name,
         csm.do_number,csm.do_date,csm.inv_date,csm.inv_num_sara,csm.inv_num_abc
         from custom_stock_move as csm where partner_id=%s and csm.issuance_date is not null and (csm.issuance_date between '%s' and '%s') order by csm.issuance_date asc,csm.dealer_name asc""" % (
        self.partner_id.id,self.date_from, self.date_to))

        result = self.env.cr.dictfetchall()
        return result

    def sale_letter_summary(self):
        result = []
        self.env.cr.execute("""
        select csm.do_number,csm.do_date,count(csm.engine_number) as total
        from custom_stock_move as csm where csm.partner_id=%s and (csm.date between '%s' and '%s') group by csm.do_number,csm.do_date
        order by csm.do_number,csm.do_date asc
        """%(str(self.partner_id.id),self.date_from,self.date_to))
        total_letters = self.env.cr.dictfetchall()

        self.env.cr.execute("""
               select csm.do_number,csm.do_date,count(csm.issuance_date) as total
               from custom_stock_move as csm where csm.partner_id=%s and (csm.date between '%s' and '%s') group by csm.do_number,csm.do_date
               order by csm.do_number,csm.do_date asc
               """ % (str(self.partner_id.id), self.date_from, self.date_to))
        issued_letters = self.env.cr.dictfetchall()

        for i in range(len(total_letters)):
            result.append({
                'do_number': total_letters[i]['do_number'],
                'do_date': total_letters[i]['do_date'],
                'total': total_letters[i]['total'],
                'issued':issued_letters[i]['total'],
                'balance': total_letters[i]['total'] - issued_letters[i]['total']
            })

        return result

    def print_report(self, cr, uid, ids, data, context=None):
        obj = self.browse(cr, uid, ids[0], context=context)
        if obj.type == 'Certificate Issuance With Invoice':
            return {
                'type': 'ir.actions.report.xml',
                'name': 'custom_inventory.certificate_issuance',
                'report_name': 'custom_inventory.certificate_issuance'
            }
        if obj.type == 'Sale Letter Summary (Remain)':
            return {
                'type': 'ir.actions.report.xml',
                'name': 'custom_inventory.sale_letter_summary_remain',
                'report_name': 'custom_inventory.sale_letter_summary_remain'
            }

