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
                                  ('Post Dated Cheque Report', 'Post Dated Cheque Report'),
                                  ('Finished Products', 'Finished Products'),
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

    def finished_products(self):
        self.env.cr.execute("""
        select pt.name as product,spl.name as engine_number,spl.chassis_number,sq.qty,spl.color,spl.model,spl.year
        from stock_production_lot as spl 
        inner join product_template as pt on spl.product_id = pt.id
        inner join stock_quant as sq on spl.id = sq.lot_id where spl.status != 'Issued' and spl.create_date between '%s' and '%s'
        """%(self.date_from,self.date_to+" 23:00:00"))
        result = self.env.cr.dictfetchall()
        return result

    def post_dated(self):
        result=[]
        account_ids = self.env['account.account'].search(
            [['type', '=', 'liquidity'], ['company_id', '=', 1]])
        for id in account_ids:
            self.env.cr.execute("""select av.number,av.date,av.cheque_date,aml.ref,aml.credit,av.cheque_no
            from account_voucher as av inner join account_move as am on av.number = am.name 
            inner join account_move_line as aml on am.id = aml.move_id where aml.credit>0 and av.type='payment'
            and aml.account_id=%s and av.cheque_date is not null and av.date between '%s' and '%s'
            order by av.date"""%(id.id,self.date_from,self.date_to))
            data = self.env.cr.dictfetchall()
            if len(data)>0:
                result.append([{'bank': id.name, 'details': data}])
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
        where stock_picking.partner_id=%s and  stock_picking.date between '%s' and '%s'"""%(self.partner_id.id,self.date_from,self.date_to+" 23:00:00"))
        result = self.env.cr.dictfetchall()
        return result

    def remaining_letter_dealer_wise(self):
        self.env.cr.execute("""
            select csm.certificate_serial as id,csm.issuance_date,csm.engine_number,csm.chassis_number,csm.dealer_name,
            csm.do_number,csm.do_date,csm.inv_date,csm.inv_num_sara,csm.inv_num_abc
            from custom_stock_move as csm where partner_id=%s and csm.counter=0 and (csm.create_date between '%s' and '%s') order by csm.create_date asc,csm.dealer_name asc""" % (
            self.partner_id.id, self.date_from, self.date_to+' 23:00:00'))

        result = self.env.cr.dictfetchall()
        return result

    def check_in_sale_summary(self,result,customer_id):
        for res in range(len(result)):
            if result[res]['id'] == customer_id:
                return res
            else:
                return False

    def sale_letter_summary(self):
        result = []
        if self.partner_id:
            self.env.cr.execute("""
            select csm.do_number,csm.do_date,count(csm.engine_number) as total
            from custom_stock_move as csm where csm.partner_id=%s and (csm.date between '%s' and '%s') group by csm.do_number,csm.do_date
            order by csm.do_number,csm.do_date asc
            """%(str(self.partner_id.id),self.date_from,self.date_to))
            total_letters = self.env.cr.dictfetchall()

            self.env.cr.execute("""
                   select csm.do_number,csm.do_date,count(csm.issuance_date) as total
                   from custom_stock_move as csm where csm.partner_id=%s and csm.issuance_date is not null and (csm.date between '%s' and '%s') group by csm.do_number,csm.do_date
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
        else:
            self.env.cr.execute("""select id,name as customer from res_partner where customer=True""")
            customers = self.env.cr.dictfetchall()
            for customer in customers:
                self.env.cr.execute("""
                            select csm.do_number,csm.do_date,count(csm.engine_number) as total
                            from custom_stock_move as csm where csm.partner_id=%s and (csm.date between '%s' and '%s') group by csm.do_number,csm.do_date
                            order by csm.do_number,csm.do_date asc
                            """ % (str(customer['id']), self.date_from, self.date_to))
                total_letters = self.env.cr.dictfetchall()

                self.env.cr.execute("""
                                   select csm.do_number,csm.do_date,count(csm.issuance_date) as total
                                   from custom_stock_move as csm where csm.partner_id=%s and csm.issuance_date is not null and (csm.date between '%s' and '%s') group by csm.do_number,csm.do_date
                                   order by csm.do_number,csm.do_date asc
                                   """ % (str(customer['id']), self.date_from, self.date_to))
                issued_letters = self.env.cr.dictfetchall()
                for i in range(len(total_letters)):
                    if len((total_letters)):
                        if len(result)== 0:
                            if len(issued_letters) > 0:
                                result.append({
                                    'id': customer['id'],
                                    'name': customer['customer'],
                                    'details': [{
                                        'do_number': total_letters[i]['do_number'],
                                        'do_date': total_letters[i]['do_date'],
                                        'total': total_letters[i]['total'],
                                        'issued':issued_letters[i]['total'],
                                        'balance': total_letters[i]['total'] - issued_letters[i]['total']
                                    }]})
                            else:
                                result.append({
                                    'id': customer['id'],
                                    'name': customer['customer'],
                                    'details': [{
                                        'do_number': total_letters[i]['do_number'],
                                        'do_date': total_letters[i]['do_date'],
                                        'total': total_letters[i]['total'],
                                        'issued': 0,
                                       'balance': total_letters[i]['total'] - 0
                                   }]})
                        else:
                            result_id = self.check_in_sale_summary(result, customer['id'])
                            if type(result_id) == int:
                                print(">>>>>>>>>>>>>>>>>>>>>>>Get",result_id)
                                result[result_id]['details'].append({
                                    'do_number': total_letters[i]['do_number'],
                                    'do_date': total_letters[i]['do_date'],
                                    'total': total_letters[i]['total'],
                                    'issued': issued_letters[i]['total'],
                                    'balance': total_letters[i]['total'] - issued_letters[i]['total']
                                })
                            else:
                                if len(issued_letters) > 0:
                                    result.append({
                                        'id': customer['id'],
                                        'name': customer['customer'],
                                        'details': [{
                                            'do_number': total_letters[i]['do_number'],
                                            'do_date': total_letters[i]['do_date'],
                                            'total': total_letters[i]['total'],
                                            'issued': issued_letters[i]['total'],
                                            'balance': total_letters[i]['total'] - issued_letters[i]['total']
                                        }]})
                                else:
                                    result.append({
                                        'id': customer['id'],
                                        'name': customer['customer'],
                                        'details': [{
                                            'do_number': total_letters[i]['do_number'],
                                            'do_date': total_letters[i]['do_date'],
                                            'total': total_letters[i]['total'],
                                            'issued': 0,
                                            'balance': total_letters[i]['total'] - 0
                                        }]})
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

        elif obj.type == 'Post Dated Cheque Report':
            return {
                'type': 'ir.actions.report.xml',
                'name': 'custom_inventory.post_dated',
                'report_name': 'custom_inventory.post_dated'
            }

        elif obj.type == 'Finished Products':
            return {
                'type': 'ir.actions.report.xml',
                'name': 'custom_inventory.manufactured_products',
                'report_name': 'custom_inventory.manufactured_products'
            }



