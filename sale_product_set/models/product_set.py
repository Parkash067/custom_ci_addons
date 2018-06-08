# -*- encoding: utf-8 -*-
from openerp import api, fields, models, _


class ProductSet(models.Model):
    _name = 'product.set'
    _description = 'Product set'

    name = fields.Char(u"Name", help=u"Product set name", required=True)
    set_line_ids = fields.One2many(
        'product.set.line', 'product_set_id', u"Products", copy=True)

    @api.multi
    def copy(self, default=None):
        if default is None:
            default = {}
        self.ensure_one()
        default['name'] = "%s %s" % (self.name, _("(copy)"), )
        return super(ProductSet, self).copy(default=default)

    @api.multi
    def create_bom(self):
        product_code = str(self.name).split(']')[0].split('[')[1].strip()
        product = self.env['product.template'].search([('default_code','=',product_code)])[0]
        bom_id = self.env['mrp.bom'].create({
            'product_tmpl_id': product.id
        })
        for product in self.set_line_ids:
            self.env['mrp.bom.line'].create({
                'product_id': product.product_id.id,
                'product_qty': product.quantity,
                'bom_id': bom_id[0].id
            })
