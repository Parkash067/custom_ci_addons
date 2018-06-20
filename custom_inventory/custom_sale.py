import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv
from openerp import api,_
import base64
import cStringIO
import qrcode


class custom_sale(osv.osv):
    _inherit = 'sale.order'
    _columns = {
        'so_type': fields.selection([('distribution', 'Materials Distribution')], 'Operation', store=True),
        'mo_reference': fields.many2one('mrp.production','MO Reference', store=True),
        'product_name': fields.related('mo_reference', 'product_id', relation="product.product", type='many2one',
                                     string="Product", store=True),
        'qty': fields.related('mo_reference', 'product_qty', type='float', string='Quantity', store=True),
    }

    # 'product': fields.many2one('mo_reference.product_id', string='Product Name',readonly=True),
    # }


class custom_sale_line(osv.osv):
    _inherit = 'sale.order.line'

    @api.onchange('product_id')
    def description(self):
        self.name = self.product_id.name
