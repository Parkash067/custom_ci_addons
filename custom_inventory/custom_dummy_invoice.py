#The file name of this file must match the filename name which we import in __init__.py file
# -*- coding: utf-8 -*-
from openerp.osv import fields, osv
from openerp import api
from datetime import date,time
from openerp.tools import amount_to_text_en
import qrcode
import cStringIO
import base64

class custom_dummy_invoice(osv.osv):
    _name = "custom.dummy.invoice"
    _rec_name = "partner_id"
    _columns = {
        'picking_id': fields.many2one('stock.picking', 'DO', store=True),
        'chassis_number': fields.char('Chassis No.'),
        'engine_number': fields.char('Engine No.'),
        'type': fields.selection([('Registered', 'For Registered Customer'),
                                  ('Unregistered', 'For Unregistered Customer'),
                                  ('sara_to_abc', 'Sara To ABC'),
                                  ('dealer_abc', 'For Dealer ABC')]
                                 , store=True, string='Type'),
        'header': fields.selection([('Sara Automobiles', 'Sara Automobiles'),
                                    ('Allied Business Corporation', 'Allied Business Corporation'),
                                    ('/', '/')], string='Header', store=True),
        'sop': fields.char('SOP', store=True),
        'sale_type': fields.char('Sale Type', store=True),
        'extra_tax': fields.float('Extra Tax', store=True),
        'rate': fields.float('Rate', store=True),
        'description': fields.char('Description', store=True),
        'hs_code': fields.char('HS Code', store=True),
        'quantity': fields.float('Quantity', store=True),
        'uom': fields.char('UOM', store=True),
        'dealer_id': fields.many2one('res.partner', 'Dealer', store=True),
        'sara_inv_serial': fields.char('Invoice #', store=True),
        'abc_inv_serial': fields.char('Invoice #', store=True),
        'partner_id': fields.char('Customer', store=True,required=True),
        'nic': fields.char('NIC', store=True),
        'ntn': fields.char('NTN', store=True),
        'address': fields.char('Address', store=True),
        'invoice_line': fields.one2many('custom.dummy.invoice.line','name','Invoice Lines',store=True),
        'ref_': fields.char('Ref',store=True),
        'date_invoice': fields.date('Invoice Date',store=True),
        'due_date': fields.date('Due Date', store=True),
        'from_': fields.date('From',store=True),
        'to_': fields.date('To',store=True),
        'amount_untaxed': fields.float('Subtotal', store=True, readonly=True, default=0.0, compute='cal_tax_and_untaxedamount'),
        'amount_tax': fields.float('Sales Tax', store=True, readonly=True, default=0.0, compute='cal_tax_and_untaxedamount'),
        'amount_total': fields.float('Total', store=True, readonly=True, default=0.0, compute='cal_total_amount'),
        'wht': fields.float('W.H.T', store=True, readonly=True, default=0.0, compute='cal_tax_and_untaxedamount'),
        'further_tax': fields.float('Further Tax', store=True, readonly=True, default=0.0, compute='cal_tax_and_untaxedamount'),
        'comment': fields.text('Comment', store=True),
        'qr_code': fields.binary('QR Code', store=True),
    }
    
    def generate_qr_code(self):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=2,
            border=4,

        )
        qr.add_data('Engine Number : ' + self.engine_number + '\n' +
                    'Chassis Number : ' + self.chassis_number + '\n' +
                    'Model : ' + '2018' + '\n' +
                    'Brand : ' + 'Union Star' + '\n' +
                    'HP : ' + '70 CC' + '\n'
                    + 'MANUFACTURED BY SARA AUTOMOBILE INDUSTRIES')
        qr.make(fit=True)
        img = qr.make_image()
        buffer = cStringIO.StringIO()
        img.save(buffer, format("PNG"))
        img_str = base64.b64encode(buffer.getvalue())
        self.write({'qr_code': img_str})
        return ''

    def create(self, cr, uid, vals, context=None):
        vals['sara_inv_serial'] = self.pool.get('ir.sequence').get(cr, uid, 'sara.inv.serial')
        vals['abc_inv_serial'] = self.pool.get('ir.sequence').get(cr, uid, 'abc.inv.serial')
        return super(custom_dummy_invoice, self).create(cr, uid, vals, context=context)

    @api.one
    @api.depends('invoice_line.price_subtotal')
    def cal_tax_and_untaxedamount(self):
        for line in self.invoice_line:
            self.amount_untaxed += line.price_subtotal
            self.amount_tax += line.sales_tax
            self.wht += line.wht
            self.further_tax += line.further_tax
        return True

    @api.one
    @api.depends('amount_untaxed','amount_tax')
    def cal_total_amount(self):
        self.amount_total = self.amount_tax + self.amount_untaxed + self.wht + self.further_tax
        return True

    @api.multi
    def amount_to_text(self, amount, currency):
        convert_amount_in_words = amount_to_text_en.amount_to_text(amount, lang='en', currency='')
        convert_amount_in_words = convert_amount_in_words.replace(' and Zero Cent', ' Only ')
        return convert_amount_in_words

    @api.multi
    def get_data(self,string):
        record_collection = []
        # Do your browse, search, calculations, .. here and then return the data (which you can then use in the QWeb)
        record_collection = self.env['logo.invoice'].search([('type', '=', string)])
        return record_collection.logo

class custom_dummy_invoice_lines(osv.osv):
    _name = "custom.dummy.invoice.line"
    _rec_name = 'products'
    _columns = {
        'name': fields.many2one('custom.dummy.invoice','Name', store=True),
        'ntn': fields.related('name', 'ntn', type='char', string='NTN', store=True),
        'nic': fields.related('name', 'nic', type='char', string='NIC', store=True),
        'sara_inv_number': fields.related('name', 'sara_inv_serial', type='char', string='Inv. No.', store=True),
        'date': fields.related('name', 'date_invoice', type='date', string='Inv. Date', store=True),
        'excl_val': fields.related('name', 'amount_untaxed', type='float', string='Excl. Value', store=True),
        'incl_val': fields.related('name', 'amount_untaxed', type='float', string='Incl. Value', store=True),
        'products': fields.char('Product', store=True),
        'quantity': fields.float('Quantity', store=True,default=0.0),
        'price_unit': fields.float('Unit Price', store=True,default=0.0),
        'sales_tax': fields.float('Sales Tax 17%', store=True,default=0.0, compute='cal_wht_further_tax'),
        'wht': fields.float('W.H.T', store=True, default=0.0, compute='cal_wht_further_tax'),
        'further_tax': fields.float('Further Tax 3%', store=True, compute='cal_wht_further_tax'),
        'price_subtotal': fields.float('Incl. Value', store=True, readonly=True,default=0.0, compute='basic_amount'),
        'chassis_number': fields.char('Chassis No.'),
        'engine_number': fields.char('Engine No.'),
    }

    @api.one
    @api.depends('quantity','price_unit')
    def basic_amount(self):
        self.price_subtotal = self.quantity * self.price_unit
        return True

    @api.one
    @api.depends('quantity', 'price_unit', 'sales_tax')
    def cal_wht_further_tax(self):
        if self.name.ntn and self.name.partner_id != 'Allied Business Corporation':
            sales_tax = round(self.price_unit * 17 / 100)
            wht = round((self.quantity * self.price_unit + sales_tax)*0.1 / 100)
            further_tax = 0
            self.sales_tax = sales_tax
            self.wht = wht
            self.further_tax = further_tax
        elif self.name.ntn == False and self.name.partner_id != 'Allied Business Corporation':
            sales_tax = round(self.price_unit * 17 / 100)
            wht = round((self.quantity * self.price_unit + sales_tax) * 0.2 / 100)
            further_tax = round(self.price_unit * 3 / 100)
            self.sales_tax = sales_tax
            self.wht = wht
            self.further_tax = further_tax
        elif self.name.partner_id == 'Allied Business Corporation':
            sales_tax = round(self.price_unit * 17 / 100)
            wht = 0
            further_tax = 0
            self.sales_tax = sales_tax
            self.wht = wht
            self.further_tax = further_tax
        return True



