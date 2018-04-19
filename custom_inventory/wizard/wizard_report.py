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
                                  ('Remaining Letter Party Wise', 'Remaining Letter Party Wise'),
                                  ('Sale Letter Summary (Remain)', 'Sale Letter Summary (Remain)'),
                                  ('Sale History', 'Sale History'),
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
      select csm.certificate_serial as id,csm.issuance_date,csm.engine_number,csm.chassis_number,csm.dealer_name,
      csm.do_number,csm.do_date,csm.inv_date,csm.inv_num_sara,csm.inv_num_abc
      from custom_stock_move as csm where csm.issuance_date is not null and (csm.issuance_date between '%s' and '%s') order by csm.issuance_date asc,csm.dealer_name asc"""%(self.date_from,self.date_to))
      result = self.env.cr.dictfetchall()
      return result

    def certificate_issuance_dealer_wise(self):
        self.env.cr.execute("""
         select csm.certificate_serial as id,csm.issuance_date,csm.engine_number,csm.chassis_number,csm.dealer_name,
         csm.do_number,csm.do_date,csm.inv_date,csm.inv_num_sara,csm.inv_num_abc
         from custom_stock_move as csm where partner_id=%s and csm.issuance_date is not null and (csm.issuance_date between '%s' and '%s') order by csm.issuance_date asc,csm.dealer_name asc""" % (
        self.partner_id.id,self.date_from, self.date_to))
        result = self.env.cr.dictfetchall()
        return result

    def sale_history(self):
        self.env.cr.execute("""select stock_picking.origin,custom_stock_move.do_number,custom_stock_move.date,
        custom_stock_move.dealer_name,product_product.name_template as item,custom_stock_move.engine_number,custom_stock_move.chassis_number,custom_stock_move.model,
        custom_stock_move.color,custom_stock_move.year,custom_stock_move.product_qty from stock_picking 
        inner join custom_stock_move 
        on stock_picking.id = custom_stock_move.picking_id
        inner join product_product on custom_stock_move.product_id = product_product.id 
        where stock_picking.partner_id=%s and  stock_picking.date between '%s' and '%s'"""%(self.partner_id.id,self.date_from,self.date_to))
        result = self.env.cr.dictfetchall()
        return result

    def remaining_letter_dealer_wise(self):
        self.env.cr.execute("""
            select csm.certificate_serial as id,csm.issuance_date,csm.engine_number,csm.chassis_number,csm.dealer_name,
            csm.do_number,csm.do_date,csm.inv_date,csm.inv_num_sara,csm.inv_num_abc
            from custom_stock_move as csm where partner_id=%s and csm.counter=0 and (csm.create_date between '%s' and '%s') order by csm.create_date asc,csm.dealer_name asc""" % (
            self.partner_id.id, self.date_from, self.date_to))

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
               from custom_stock_move as csm where csm.partner_id=%s and csm.issuance_date is not null (csm.date between '%s' and '%s') group by csm.do_number,csm.do_date
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
        if obj.type == 'Certificate Issuance With Invoice Date Wise' or obj.type == 'Certificate Issuance With Invoice Dealer Wise' or \
                obj.type == 'Remaining Letter Party Wise':
            return {
                'type': 'ir.actions.report.xml',
                'name': 'custom_inventory.certificate_issuance',
                'report_name': 'custom_inventory.certificate_issuance'
            }
        elif obj.type == 'Sale Letter Summary (Remain)':
            return {
                'type': 'ir.actions.report.xml',
                'name': 'custom_inventory.sale_letter_summary_remain',
                'report_name': 'custom_inventory.sale_letter_summary_remain'
            }

        elif obj.type == 'Sale History':
            return {
                'type': 'ir.actions.report.xml',
                'name': 'custom_inventory.sale_history',
                'report_name': 'custom_inventory.sale_history'
            }


