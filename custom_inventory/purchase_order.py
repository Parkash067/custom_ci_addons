import itertools
import math
from lxml import etree

from openerp import models, fields, api, _
from openerp.osv import fields as field, osv
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp


class po_invoice_line(models.Model):
    _inherit = "account.invoice"

    sto = fields.Float('STO', store=True)
    sti = fields.Float('STI', store=True)
    et = fields.Float('ET', store=True)
    stwh = fields.Float('STWH', store=True)
    gst = fields.Float('GST', store=True)

    @api.multi
    def button_reset_taxes(self):
        for i in self.tax_line:
            if i.name == 'OUTPUT TAX 17.00%':
                self.sto = float(i.amount)
            elif i['name'] == 'INPUT TAX 17.00%':
                self.sti = float(i.amount)
            elif i['name'] == 'EXTRA TAX 2%':
                self.et = float(i.amount)
            elif i['name'] == 'SALES TAX WITH HELD':
                self.stwh = float(i.amount)
            elif i['name'] == 'GST 17%':
                self.gst = float(i.amount)
        return True


class po(models.Model):
    _inherit = "purchase.order"

    tax_line = fields.One2many('po.taxes', 'po_id', string='Tax Lines',
                               readonly=True, states={'draft': [('readonly', False)]}, copy=True)
    @api.multi
    def button_reset_taxes(self):
        taxes_list = []
        for line in self.order_line:
            for taxes in line.taxes_id:
                taxes_list.append({'name': taxes.name, 'amount': taxes.amount * line.price_subtotal})
        self._cr.execute("DELETE FROM po_taxes WHERE po_id=%s", (self.id,))
        self.invalidate_cache()
        for i in taxes_list:
            self.env['po.taxes'].create({'po_id': self.id, 'name': i['name'], 'amount': i['amount']})
            if i['name'] == 'OUTPUT TAX 17.00%':
                self.sto = float(i['amount'])
            elif i['name'] == 'INPUT TAX 17.00%':
                self.sti = float(i['amount'])
            elif i['name'] == 'EXTRA TAX 2%':
                self.et = float(i['amount'])
            elif i['name'] == 'SALES TAX WITH HELD':
                self.stwh = float(i['amount'])
            elif i['name'] == 'GST 17%':
                self.gst = float(i['amount'])


class po_order_taxes(models.Model):
    _name = "po.taxes"
    _description = "Break up taxes on PO"

    po_id = fields.Many2one('purchase.order', string='Invoice Line',
                            ondelete='cascade', index=True)
    name = fields.Char(string='Tax Description',
                       required=True)
    amount = fields.Float(string='Amount', digits=dp.get_precision('Account'))


class custom_price_list(models.Model):
    _name = "purchase.price.list"

    name = fields.Char('Product Name', store=True)
    code = fields.Char('Code', store=True)
    price = fields.Float('price', store=True)


class po_line(osv.osv):
    _inherit = "purchase.order.line"
    _columns = {
        'product_id': field.many2one('product.product', 'Product', domain=[('purchase_ok', '=', True)],
                                      change_default=True),
    }

    @api.onchange('product_id')
    def cal_price(self):
        if self.product_id == False:
            return None
        data = self.env['purchase.price.list'].search([('code', '=', self.product_id.default_code)])
        self.price_unit = data.price if len(data) > 0 else 0.0
        self.name = self.product_id.name
        self.date_planned = self.order_id.date_order

    @api.onchange('product_qty')
    def cal_qty_price(self):
        if self.product_id == False:
            return None
        data = self.env['purchase.price.list'].search([('code', '=', self.product_id.default_code)])
        print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        self.price_unit = data.price*self.product_qty if len(data) > 0 else 0.0


