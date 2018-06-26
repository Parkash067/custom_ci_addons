import itertools
import math
from lxml import etree

from openerp import models, fields, api, _
from openerp.osv import fields as field, osv
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp


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

