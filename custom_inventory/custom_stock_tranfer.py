from openerp import models,fields,api,_
from openerp.osv import fields,osv
from datetime import datetime


class custom_stock_transfer_details_items(osv.TransientModel):
    _inherit = 'stock.transfer_details_items'
    _columns = {
        'chassis_number': fields.char('Chassis No.'),
        'engine_number': fields.char('Engine No.'),
        'color': fields.char('Color'),
        'model': fields.char('Model'),
        'year': fields.char('Year'),
        'location': fields.boolean('Loc'),
    }

    _defaults = {
        'chassis_number': 'SAC-',
        'engine_number': 'SAE-',
    }


class custom_stock_transfer_details(osv.TransientModel):
    _inherit = 'stock.transfer_details'
    _description = 'Picking wizard'
    _columns = {

    }

    @api.one
    def do_detailed_transfer(self):
        order_id = {}
        if self.picking_id.state not in ['assigned', 'partially_available']:
            raise Warning(_('You cannot transfer a picking in state \'%s\'.') % self.picking_id.state)
        stock_wh_obj = self.env['stock.warehouse'].search([('name', '=', 'Allied Business Corporation')])
        picking_id = self.env['stock.picking.type'].search([('name', '=', 'Receipts'),
                                                            ('warehouse_id', '=', stock_wh_obj.id)])
        if self.picking_id.partner_id.name == 'Allied Business Corporation':
            purchase_order = {
                'partner_id': 1497,
                'company_id': 3,
                'picking_type_id': picking_id.id,
                'location_id': 116,
                'date_order': fields.datetime.now(),
                'invoice_method': 'picking',
                'pricelist_id': 2,
            }
            order_id = self.env['purchase.order'].create(purchase_order)
        processed_ids = []
        # Create new and update existing pack operations
        for lstits in [self.item_ids, self.packop_ids]:
            for prod in lstits:
                pack_datas = {
                    'product_id': prod.product_id.id,
                    'product_uom_id': prod.product_uom_id.id,
                    'product_qty': prod.quantity,
                    'package_id': prod.package_id.id,
                    'lot_id': prod.lot_id.id,
                    'location_id': prod.sourceloc_id.id,
                    'location_dest_id': prod.destinationloc_id.id,
                    'result_package_id': prod.result_package_id.id,
                    'date': prod.date if prod.date else datetime.now(),
                    'owner_id': prod.owner_id.id,
                    'engine_no': prod.engine_number
                }
                if self.picking_id.partner_id.customer:
                    stock_moves = {
                        'engine_number': prod.lot_id.name,
                        'chassis_number': prod.lot_id.chassis_number,
                        'color': prod.lot_id.color,
                        'model': prod.lot_id.model,
                        'year': prod.lot_id.year,
                        'picking_id': self.picking_id.id,
                        'partner_id': self.picking_id.partner_id.id,
                        'product_id': prod.product_id.id,
                        'product_qty': prod.quantity,
                        'date': prod.date if prod.date else datetime.now(),
                    }
                    self.env['custom.stock.move'].create(stock_moves)
                    self.env.cr.execute("""update stock_production_lot set status='%s' where name='%s'"""%('Issued',prod.lot_id.name))
                    if self.picking_id.partner_id.name == 'Allied Business Corporation':
                        purchase_order_lines = {
                            'product_id': 6,
                            'name': prod.product_id.name,
                            'product_uom': prod.product_uom_id.id,
                            'product_qty': prod.quantity,
                            'price_unit': prod.product_id.standard_price,
                            'date_planned': fields.datetime.now(),
                            'order_id': order_id.id
                        }
                        self.env['purchase.order.line'].create(purchase_order_lines)
                if prod.packop_id:
                    prod.packop_id.with_context(no_recompute=True).write(pack_datas)
                    processed_ids.append(prod.packop_id.id)
                else:
                    pack_datas['picking_id'] = self.picking_id.id
                    packop_id = self.env['stock.pack.operation'].create(pack_datas)
                    processed_ids.append(packop_id.id)
        # Delete the others
        packops = self.env['stock.pack.operation'].search(['&', ('picking_id', '=', self.picking_id.id), '!', ('id', 'in', processed_ids)])
        packops.unlink()

        # Execute the transfer of the picking
        self.picking_id.do_transfer()

        return True


