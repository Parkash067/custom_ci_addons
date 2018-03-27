from openerp import models,fields,api
from openerp.osv import fields,osv
from datetime import date, timedelta,datetime
import xlwt
import StringIO
import base64

sales_register = ['Sr.No.', 'NTN', 'NIC', 'Buyer\'s Name', 'Description', 'Engine Number', 'Chassis Number',
                  'Inv No.', 'Inv Date', 'Excl Value', 'Futher Tax', 'S.T.Value', 'Incl.Value']

annex_c = ['Sr.No.', 'Buyer\'s NTN', 'Buyer\'s NIC', 'Buyer\'s Name', 'Buyer\'s Type', 'Sale Organisation Province of Supplier',
           'Document Type', 'Document Number','Document Date','HS Code','Sale Type', 'Rate', 'Description', 'Quantity', 'UOM',
           'Value of Sales Excluding Sales Tax', 'Sales Tax/FED in ST Mode','Extra Tax','ST Withheld at Source','SRO No./ Schedule No.','Item Sr. No.','Further Tax','Total Value of Sales']

income_tax = ['Sr.No', 'Taxpayer NTN', 'Taxpayer Name / Business Name','Taxpayer Address','Payment Nature','Payment Section Code',
              'Payment Date','Cheque No. & Date', 'Bank Name','Taxable Amount','Tax Rate', 'Tax Amount', 'Deposite Date']

purchase_register = ['Sr.No', 'NTN#', 'Name of the Supplier', 'Address', 'Item Description','Invoice No.',
              'Invoice Date', 'Quantity', 'Rate', 'Val Excl. S.Tax','Sales Tax 17%', 'Val Inc. S.Tax', 'With Held 20%']


class demo_xls_report_file(osv.osv_memory):
    _name = 'demo.xls.report.file'
    _description = 'PDF Reports for showing all disconnection,reconnection'

    _columns = {
        'file': fields.binary('File'),
        'file_name': fields.char('File Name', size=64),

    }

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        res = super(demo_xls_report_file, self).default_get(cr, uid, fields, context=context)
        res.update({'file_name': 'Report.xls'})
        if context.get('file'):
            res.update({'file': context['file']})
        return res


class xls_report(osv.osv):
    _name = 'xls.report'
    _columns = {
        'type': fields.selection([('IncomeTax Report', 'IncomeTax Report'),
                                  ('Purchase Register', 'Purchase Register'),
                                  ('Sales Register', 'Sales Register'),
                                  ('Annex C', 'Annex C'),
                                  ('Collection Report', 'Collection Report'),
                                  ('Individual Aging', 'Individual Aging'),
                                  ('/','/')], 'Report Type', required=True),
        'date_from': fields.date('From', required=True),
        'date_to': fields.date('To', required=True),
        'company_id': fields.many2one('res.company', 'Company'),
        'partner_id': fields.many2one('res.partner', 'Customer', domain=[('customer','=','True')]),
    }

    _defaults = {
        'date_from': lambda *a: datetime.now().strftime('%Y-%m-%d'),
        'date_to': lambda *a: datetime.now().strftime('%Y-%m-%d'),
        'type': '/'
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
        if self.multiple_customers == False:
            self.env.cr.execute(
                "select account_invoice.number,account_invoice.partner_id,account_invoice.date_invoice,account_invoice.amount_total from account_invoice where account_invoice.date_invoice between'" + str(
                    self.date_from) + "'" + " and '" + str(
                    self.date_to) + "'" + "and state='open'" + "and account_invoice.company_id=" + str(
                    self.company_id.id) + "order by account_invoice.date_invoice")
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

    def sales_register_report(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context=context)
        cr.execute(
            "select sales_register.ntn,sales_register.nic,sales_register.name,sales_register.products,sales_register.engine_number,sales_register.chassis_number,"
            "sales_register.sara_inv_number,sales_register.date,sales_register.excl_val,sales_register.further_tax,sales_register.sales_tax,"
            "sales_register.price_subtotal from custom_dummy_invoice_line as sales_register where sales_register.date between'" + str(
                obj.date_from) + "'" + " and '" + str(
                obj.date_to) + "'" + "order by sales_register.date")
        data = cr.dictfetchall()
        return data

    def annex_c_report(self, cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context=context)
        cr.execute(
            "select rp.ntn,rp.nic,rp.name,rp.taxation,cdi.amount_untaxed,cdi.date_invoice,cdi.sara_inv_serial,cdi.amount_tax,cdi.amount_total,cdi.further_tax from custom_dummy_invoice as cdi inner join res_partner as rp on cdi.dealer_id = rp.id where cdi.date_invoice between'" + str(
                obj.date_from) + "'" + " and '" + str(
                obj.date_to) + "'" + "order by cdi.date_invoice asc")
        data = cr.dictfetchall()
        return data

    def income_tax_report(self,cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context=context)
        cr.execute(
            "select rp.ntn,rp.name,rp.street,rp.city,aml.date,aml.ref,aml.move_id,aml.credit from account_move_line as aml inner join res_partner as rp on aml.partner_id = rp.id where aml.date between'" + str(
                obj.date_from) + "'" + " and '" + str(
                obj.date_to) + "'" + "and aml.credit > 0 and aml.account_id=213order by aml.date asc")
        data = cr.dictfetchall()
        return data

    def purchase_register_report(self,cr, uid, ids, context=None):
        obj = self.browse(cr, uid, ids[0], context=context)
        cr.execute(
            "select rp.ntn,rp.name,rp.street,rp.city,av.date_invoice,av.amount_tax,av.number,av.amount_total,av.amount_untaxed,avl.quantity,avl.price_unit from account_invoice as av inner join res_partner as rp on av.partner_id = rp.id "
            "inner join account_invoice_line as avl on av.id = avl.invoice_id where av.date_invoice between'" + str(
                obj.date_from) + "'" + " and '" + str(
                obj.date_to) + "'" + "order by date_invoice asc")
        data = cr.dictfetchall()
        return data

    def report_xls(self, cr, uid, ids, context=None):
        if self.check_dates(cr, uid, ids, context=None):
            obj = self.browse(cr, uid, ids[0], context=context)
            fl = StringIO.StringIO()
            if context is None: context = {}
            wb = xlwt.Workbook()
            ws = wb.add_sheet('Report')
            font = xlwt.Font()
            font.bold = True
            borders = xlwt.Borders()
            bold_style = xlwt.XFStyle()
            bold_style.font = font
            new_style7 = xlwt.easyxf('font:height 210; font:name Calibri; align:wrap No;')
            borders.bottom = xlwt.Borders.THICK
            # ws.col(1).width = 500 * 12
            # ws.row(5).height = 70 * 5
            if obj.type == 'Sales Register':
                for i in range(len(sales_register)):
                     ws.write(0, i,sales_register[i], new_style7)
                data = self.sales_register_report(cr,uid,ids,context=context)
                rows = len(data)
                if rows >0:
                    for i in range(len(data)):
                        ws.write(i+1, 0, i+1, new_style7)
                        ws.write(i+1, 1, data[i]['ntn'], new_style7)
                        ws.write(i+1, 2, data[i]['nic'], new_style7)
                        ws.write(i+1, 3, data[i]['name'], new_style7)
                        ws.write(i+1, 4, data[i]['products'], new_style7)
                        ws.write(i+1, 5, data[i]['engine_number'], new_style7)
                        ws.write(i+1, 6, data[i]['chassis_number'], new_style7)
                        ws.write(i+1, 7, data[i]['sara_inv_number'], new_style7)
                        ws.write(i+1, 8, data[i]['date'], new_style7)
                        ws.write(i+1, 9, data[i]['excl_val'], new_style7)
                        ws.write(i+1, 10, data[i]['further_tax'], new_style7)
                        ws.write(i+1, 11, data[i]['sales_tax'], new_style7)
                        ws.write(i+1, 12, data[i]['price_subtotal'], new_style7)

            elif obj.type == 'Purchase Register':
                for i in range(len(purchase_register)):
                    ws.write(0, i, purchase_register[i], new_style7)
                data = self.purchase_register_report(cr, uid, ids, context=context)
                rows = len(data)
                if rows > 0:
                    for i in range(len(data)):
                        ws.write(i + 1, 0, i + 1, new_style7)
                        ws.write(i + 1, 1, data[i]['ntn'], new_style7)
                        ws.write(i + 1, 2, data[i]['name'], new_style7)
                        ws.write(i + 1, 3, str(data[i]['street']) + str(data[i]['city']), new_style7)
                        ws.write(i + 1, 4, '', new_style7)
                        ws.write(i + 1, 5,data[i]['number'],new_style7)
                        ws.write(i + 1, 6, data[i]['date_invoice'], new_style7)
                        ws.write(i + 1, 7, data[i]['quantity'], new_style7)
                        ws.write(i + 1, 8, data[i]['price_unit'], new_style7)
                        ws.write(i + 1, 9, data[i]['amount_untaxed'], new_style7)
                        ws.write(i + 1, 10, data[i]['amount_tax'], new_style7)
                        ws.write(i + 1, 11, data[i]['amount_total'], new_style7)
                        ws.write(i + 1, 12, '', new_style7)

            elif obj.type == 'IncomeTax Report':
                for i in range(len(income_tax)):
                    ws.write(0, i, income_tax[i], new_style7)
                data = self.income_tax_report(cr, uid, ids, context=context)
                rows = len(data)
                if rows >0:
                    for i in range(len(data)):
                        ws.write(i+1, 0, i+1, new_style7)
                        ws.write(i+1, 1, data[i]['ntn'], new_style7)
                        ws.write(i+1, 2, data[i]['name'], new_style7)
                        ws.write(i+1, 3, str(data[i]['street'])+str(data[i]['city']), new_style7)
                        ws.write(i+1, 4, '', new_style7)
                        ws.write(i+1, 5, '', new_style7)
                        ws.write(i+1, 6, data[i]['date'], new_style7)
                        ws.write(i+1, 7, data[i]['ref'], new_style7)
                        ws.write(i + 1, 8, '', new_style7)
                        ws.write(i + 1, 9, '', new_style7)
                        ws.write(i+1, 10, '', new_style7)
                        ws.write(i+1, 11, data[i]['credit'], new_style7)
                        ws.write(i+1, 12, '', new_style7)

            elif obj.type == 'Annex C':
                for i in range(len(annex_c)):
                     ws.write(0, i, annex_c[i], new_style7)
                data = self.annex_c_report(cr,uid,ids,context=context)
                rows = len(data)
                if rows >0:
                    for i in range(len(data)):
                        ws.write(i+1, 0, i+1, new_style7)
                        ws.write(i+1, 1, data[i]['ntn'], new_style7)
                        ws.write(i+1, 2, data[i]['nic'], new_style7)
                        ws.write(i+1, 3, data[i]['name'], new_style7)
                        ws.write(i+1, 4, data[i]['taxation'], new_style7)
                        ws.write(i+1, 5, '', new_style7)
                        ws.write(i+1, 6, 'SI', new_style7)
                        ws.write(i+1, 7, data[i]['sara_inv_serial'], new_style7)
                        ws.write(i+1, 8, data[i]['date_invoice'], new_style7)
                        ws.write(i+1, 9, '', new_style7)
                        ws.write(i+1, 10, '', new_style7)
                        ws.write(i+1, 11, '', new_style7)
                        ws.write(i+1, 12, '', new_style7)
                        ws.write(i+1, 13, '', new_style7)
                        ws.write(i+1, 14, '', new_style7)
                        ws.write(i+1, 15, data[i]['amount_untaxed'], new_style7)
                        ws.write(i+1, 16, data[i]['amount_tax'], new_style7)
                        ws.write(i+1, 17, '', new_style7)
                        ws.write(i+1, 18, '', new_style7)
                        ws.write(i+1, 19, '', new_style7)
                        ws.write(i+1, 20, '', new_style7)
                        ws.write(i+1, 21, data[i]['further_tax'], new_style7)
                        ws.write(i+1, 22, data[i]['amount_total'], new_style7)

            wb.save(fl)
            fl.seek(0)
            buf = base64.encodestring(fl.read())
            ctx = dict(context)
            ctx.update({'file': buf})
            if context is None:
                context = {}
            data = {}
            res = self.read(cr, uid, ids, [], context=context)
            res = res and res[0] or {}
            data['form'] = res
            try:
                form_id = \
                self.pool.get('ir.model.data').get_object_reference(cr, uid, 'report_xls', 'view_xls_file_form_view')[1]
            except ValueError:
                form_id = False
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'demo.xls.report.file',
                'views': [(form_id, 'form')],
                'view_id': form_id,
                'targer': 'new',
                'context': ctx
            }
