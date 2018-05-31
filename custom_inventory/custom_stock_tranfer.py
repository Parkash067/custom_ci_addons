from openerp import models,fields,api,_
from openerp.osv import fields,osv
from datetime import datetime


class custom_stock_transfer_details_items(osv.TransientModel):
    _inherit = 'stock.transfer_details_items'
    _columns = {
        'chassis_number': fields.char('Chassis Number'),
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

    @api.onchange('lot_id')
    def fetch_info(self):
        if self.lot_id:
            self.chassis_number = self.lot_id.chassis_number
            self.color = self.lot_id.color
            self.model = self.lot_id.model
            self.year =  self.lot_id.year

    @api.multi
    def split_quantities(self):
        for det in self:
            if det.quantity > 1:
                det.quantity = (det.quantity - 1)
                new_id = det.copy(context=self.env.context)
                new_id.quantity = 1
                new_id.packop_id = False
                self.split_quantities()
        if self and self[0]:
            return self[0].transfer_id.wizard_view()


class custom_stock_transfer_details(osv.TransientModel):
    _inherit = 'stock.transfer_details'
    _description = 'Picking wizard'
    _columns = {
        'total_quantity': fields.float('Total Quantity'),
        'selected_quantity': fields.float('Selected Quantity', compute='select_quantity'),
    }

    @api.one
    @api.depends('item_ids.quantity')
    def select_quantity(self):
        self.selected_quantity = 0
        for item in self.item_ids:
            self.selected_quantity += item.quantity

    def default_get(self, cr, uid, fields, context=None):
        count = 0
        if context is None: context = {}
        res = super(custom_stock_transfer_details, self).default_get(cr, uid, fields, context=context)
        picking_ids = context.get('active_ids', [])
        active_model = context.get('active_model')

        if not picking_ids or len(picking_ids) != 1:
            # Partial Picking Processing may only be done for one picking at a time
            return res
        assert active_model in ('stock.picking'), 'Bad context propagation'
        picking_id, = picking_ids
        picking = self.pool.get('stock.picking').browse(cr, uid, picking_id, context=context)
        items = []
        packs = []
        if not picking.pack_operation_ids:
            picking.do_prepare_partial()
        for op in picking.pack_operation_ids:
            item = {
                'packop_id': op.id,
                'product_id': op.product_id.id,
                'product_uom_id': op.product_uom_id.id,
                'quantity': op.product_qty,
                'package_id': op.package_id.id,
                'lot_id': op.lot_id.id,
                'sourceloc_id': op.location_id.id,
                'destinationloc_id': op.location_dest_id.id,
                'result_package_id': op.result_package_id.id,
                'date': op.date,
                'owner_id': op.owner_id.id,
            }
            count += op.product_qty
            if op.product_id:
                items.append(item)
            elif op.package_id:
                packs.append(item)
        res.update(item_ids=items, total_quantity=count)
        res.update(packop_ids=packs)
        return res

    def check_quantity(self):
        if self.selected_quantity <= self.total_quantity:
            return True
        else:
            if self.selected_quantity <= self.total_quantity:
                return True
            else:
                return False

    @api.one
    def do_detailed_transfer(self):
        if self.check_quantity():
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
                    if self.picking_id.partner_id.customer and self.picking_id.picking_type_id.name == 'Receipts':
                        self.env.cr.execute("""update stock_production_lot set status='%s' where name='%s'""" % (
                        'Available', prod.lot_id.name))

                    if self.picking_id.partner_id.customer and self.picking_id.picking_type_id.name=='Delivery Orders' and self.picking_id.partner_id.custom_type != 'department':
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

        else:
            raise osv.except_osv(_('Warning!'), _('You cannot transfer items more than DO/PO'))


