import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv
from openerp import api, _
import base64
import cStringIO
import qrcode


class custom_sale(osv.osv):
    _inherit = 'sale.order'
    _columns = {
        'product_set': fields.char('Product Set', store=True),
        'so_type': fields.selection([('distribution', 'Materials Distribution')], 'Operation', store=True),
        'mo_reference': fields.many2one('mrp.production', 'MO Reference', store=True),
        'product_name': fields.related('mo_reference', 'product_id', relation="product.product", type='many2one',
                                       string="Product", store=True),
        'qty': fields.related('mo_reference', 'product_qty', type='float', string='Quantity', store=True),
        'status': fields.selection([('draft', 'Draft'), ('done', 'Done')], string='Status', store=True,
                                   compute='fetch_status')
    }

    def create(self, cr, uid, vals, context=None):
        if 'so_type' in vals:
            if vals['so_type'] == 'distribution':
                vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'mat.dis.serial')
        return super(custom_sale, self).create(cr, uid, vals, context=context)

    @api.one
    @api.depends('state')
    def fetch_status(self):
        if self.so_type == 'distribution':
            if self.state == 'draft':
                self.status = 'draft'
            elif self.state == 'progress':
                self.status = 'done'

    @api.multi
    def fetch_products(self):
        if self.mo_reference:
            self._cr.execute("DELETE FROM sale_order_line WHERE order_id=%s", (self.id,))
            product_code = str(self.mo_reference.product_id.default_code).strip()
            product = self.env['product.set'].search([('name', 'like', product_code)])[0]
            for _product in product.set_line_ids:
                self.env['sale.order.line'].create({
                    'product_id': _product.product_id.id,
                    'product_uom_qty': _product.quantity*self.mo_reference.product_qty,
                    'name': _product.product_id.name,
                    'order_id': self.id,
                })


# 'product': fields.many2one('mo_reference.product_id', string='Product Name',readonly=True),
# }


class custom_sale_line(osv.osv):
    _inherit = 'sale.order.line'

    @api.onchange('product_id')
    def description(self):
        self.name = self.product_id.name
