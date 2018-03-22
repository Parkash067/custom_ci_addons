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
        if self.picking_id.state not in ['assigned', 'partially_available']:
            raise Warning(_('You cannot transfer a picking in state \'%s\'.') % self.picking_id.state)

        processed_ids = []
        # Create new and update existing pack operations
        for lstits in [self.item_ids, self.packop_ids]:
            for prod in lstits:
                print prod
                print prod.engine_number
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
                        'engine_number': prod.engine_number,
                        'chassis_number': prod.chassis_number,
                        'color': prod.color,
                        'model': prod.model,
                        'year': prod.model,
                        'picking_id': self.picking_id.id,
                        'partner_id': self.picking_id.partner_id.id,
                        'product_id': prod.product_id.id,
                        'product_qty': prod.quantity,
                        'date': prod.date if prod.date else datetime.now(),
                    }
                    stock_move_id = self.env['custom.stock.move'].create(stock_moves)
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


