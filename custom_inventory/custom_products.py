#The file name of this file must match the filename name which we import in __init__.py file
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv
from openerp import api,_


class custom_stock_picking(osv.osv):
    _inherit = 'stock.picking'
    _columns = {
        'do_ref': fields.many2one('stock.picking','DO Reference', store=True),
        'claim_ref': fields.many2one('stock.picking', 'Claim Reference', store=True, domain="[('custom_move_type','=','File Claim')]"),
        'stock_split_lines': fields.one2many('custom.stock.move', 'picking_id', 'Stock Splits', store=True),
        'custom_move_type': fields.selection([('File Claim', 'File Claim'), ('Return against claim', 'Return against claim')], string='Move Type', store=True)
    }

    @api.onchange('custom_move_type')
    def assign_picking_type(self):
        wh_id = self.env['stock.warehouse'].search([['name', '=', 'Sara Automobiles'], ])
        if self.custom_move_type == 'File Claim':
            picking_id = self.env['stock.picking.type'].search([['name', '=', 'Delivery Orders'],['warehouse_id', '=', wh_id.id]])
            self.picking_type_id = picking_id
        elif self.custom_move_type == 'Return against claim':
            picking_id = self.env['stock.picking.type'].search([['name', '=', 'Receipts'], ['warehouse_id', '=', wh_id.id]])
            self.picking_type_id = picking_id


class custom_stock_move(osv.osv):
    _name = 'custom.stock.move'
    _rec_name = 'picking_id'
    _columns = {
        'certificate_serial': fields.char('Serial', store=True),
        'certificate_issuance': fields.integer('Issuance Times', store=True),
        'counter': fields.integer('Counter', store=True),
        'status': fields.selection([('draft', 'Draft'),
                                    ('Request for Certificate','Request for Certificate'),
                                    ('Approved','Approved')], string='State',store=True),
        'client_name': fields.char('Name', store=True),
        'nic': fields.char('NIC', store=True),
        'ntn': fields.char('NTN', store=True),
        'address': fields.char('Address', store=True),
        'certificate_lock': fields.boolean('Lock', store=True),
        'engine_number': fields.char('Engine No.', store=True),
        'chassis_number': fields.char('Chassis No.', store=True),
        'picking_id': fields.many2one('stock.picking', 'DO', store=True),
        'partner_id': fields.many2one('res.partner', 'Dealer', store=True),
        'product_id': fields.many2one('product.template', 'Product', store=True),
        'product_qty': fields.float('Quantity', store=True),
        'date': fields.datetime('Date', store=True),
        'color': fields.char('Color',store=True),
        'model': fields.char('Model',store=True),
        'year': fields.char('Year',store=True),
        'issuance_date': fields.date('Issuance Date', store=True),
        'reason': fields.text('Reason',store=True),
    }

    _defaults = {
        'certificate_issuance': 0,
        'counter': 0,
        'status': 'draft',
        'certificate_lock': False
    }

    def create(self, cr, uid, vals, context=None):
        vals['certificate_serial'] = self.pool.get('ir.sequence').get(cr, uid, 'certificate.serial')
        return super(custom_stock_move, self).create(cr, uid, vals, context=context)

    @api.multi
    def validate(self):
        if self.counter == 0:
            raise osv.except_osv(_('Warning!'), _(
                'You cannot sent it for request.\n You can print it for first time'))
        else:
            return self.write({'status': 'Request for Certificate'})

    @api.multi
    def cancel(self):
        return self.write({'status': 'draft'})

    @api.multi
    def approve(self):
        return self.write({'status': 'Approved', 'certificate_lock': False})

    def inc_in_counter(self):
        counter = int(self.counter) + 1
        self.write({'counter': counter, 'certificate_lock': True, 'issuance_date': fields.datetime.now()})

    def generate_qr_code(self):
        # return "Product Name : " + str(self.product_id.name)
        return "Engine Number : "+str(self.engine_number) + "\n" + "Chasis Number : " + str(self.chassis_number) + "\n" + "Model : " + self.model + "\n"+ "Brand : " + 'Union Start' + "\n" +"HP : " + '70' + "\n" +" 'MANUFACTURED BY SARA AUTOMOBILE INDUSTERIES'"

    def issuance(self):
        self.certificate_issuance = 1
        return ''

    def check_issuance(self):
        return int(self.certificate_issuance)

    def create_view_invoice(self, cr, uid, ids, context=None):
        inv_ids = 0
        sp = 0.0
        """ create invoices for the active sales orders """
        config_obj = self.pool.get('custom.cert.inv.config')
        _self = self.browse(cr, uid, ids[0], context=context)
        if _self.ntn == False and _self.client_name != 'Allied Businees Corporation' and _self.partner_id.name != 'Allied Business Corporation':
            inv_obj = self.pool.get('custom.dummy.invoice')
            inv_obj_line = self.pool.get('custom.dummy.invoice.line')
            inv_vals = {
                'dealer_id': _self.partner_id.id,
                'partner_id': _self.client_name,
                'date_invoice': fields.datetime.now(),
                'ntn': _self.ntn,
                'nic': _self.nic,
                'address': _self.address
            }
            inv_ids = inv_obj.create(cr, uid, inv_vals, context=context)
            prices = config_obj.search(cr, uid, [('type', '=', 'Unregistered')])
            for price in config_obj.browse(cr, uid, prices, context=context):
                sp = price.price
            inv_lines_vals = {
                'name': inv_ids,
                'products': _self.product_id.name,
                'quantity': _self.product_qty,
                'price_unit': sp,
                'chassis_number': _self.chassis_number,
                'engine_number': _self.engine_number,
            }
            inv_obj_line.create(cr,uid,inv_lines_vals,context=context)
        elif _self.ntn != False and _self.client_name != 'Allied Businees Corporation' and _self.partner_id.name != 'Allied Business Corporation':
            inv_obj = self.pool.get('custom.dummy.invoice')
            inv_obj_line = self.pool.get('custom.dummy.invoice.line')
            inv_vals = {
                'dealer_id': _self.partner_id.id,
                'partner_id': _self.client_name,
                'date_invoice': fields.datetime.now(),
                'ntn': _self.ntn,
                'nic': _self.nic,
                'address': _self.address
            }
            inv_ids = inv_obj.create(cr, uid, inv_vals, context=context)
            prices = config_obj.search(cr, uid, [('type', '=', 'Registered')])
            for price in config_obj.browse(cr, uid, prices, context=context):
                sp = price.price
            inv_lines_vals = {
                'name': inv_ids,
                'products': _self.product_id.name,
                'quantity': _self.product_qty,
                'price_unit': sp,
                'chassis_number': _self.chassis_number,
                'engine_number': _self.engine_number,
            }
            inv_obj_line.create(cr, uid, inv_lines_vals, context=context)
        elif _self.client_name == 'Allied Business Corporation' and _self.partner_id.name != 'Allied Business Corporation':
            inv_obj = self.pool.get('custom.dummy.invoice')
            inv_obj_line = self.pool.get('custom.dummy.invoice.line')
            inv_vals = {
                'dealer_id': _self.partner_id.id,
                'partner_id': _self.client_name,
                'date_invoice': fields.datetime.now(),
                'ntn': _self.ntn,
                'nic': _self.nic,
                'address': _self.address
            }
            inv_ids = inv_obj.create(cr, uid, inv_vals, context=context)
            prices = config_obj.search(cr, uid, [('type', '=', 'sara_to_abc')])
            for price in config_obj.browse(cr, uid, prices, context=context):
                sp = price.price
            inv_lines_vals = {
                'name': inv_ids,
                'products': _self.product_id.name,
                'quantity': _self.product_qty,
                'price_unit': sp,
                'chassis_number': _self.chassis_number,
                'engine_number': _self.engine_number,
            }
            inv_obj_line.create(cr, uid, inv_lines_vals, context=context)
        elif _self.partner_id.name == 'Allied Business Corporation':
            types = ['dealer_abc', 'sara_to_abc']
            for type in types:
                if type == 'dealer_abc':
                    ">>>>>>>>>>>>>>>>>>print>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
                    inv_obj = self.pool.get('custom.dummy.invoice')
                    inv_obj_line = self.pool.get('custom.dummy.invoice.line')
                    inv_vals = {
                        'dealer_id': _self.partner_id.id,
                        'partner_id': _self.client_name,
                        'date_invoice': fields.datetime.now(),
                        'ntn': _self.ntn,
                        'nic': _self.nic,
                        'address': _self.address
                    }
                    inv_ids = inv_obj.create(cr, uid, inv_vals, context=context)
                    prices = config_obj.search(cr, uid, [('type', '=', type)])
                    for price in config_obj.browse(cr, uid, prices, context=context):
                        sp = price.price
                    inv_lines_vals = {
                        'name': inv_ids,
                        'products': _self.product_id.name,
                        'quantity': _self.product_qty,
                        'price_unit': sp,
                        'chassis_number': _self.chassis_number,
                        'engine_number': _self.engine_number,
                    }
                    inv_obj_line.create(cr, uid, inv_lines_vals, context=context)
                else:
                    inv_obj = self.pool.get('custom.dummy.invoice')
                    inv_obj_line = self.pool.get('custom.dummy.invoice.line')
                    inv_vals = {
                        'partner_id': 'Allied Business Corporation',
                        'date_invoice': fields.datetime.now(),
                        'ntn': _self.ntn,
                        'nic': _self.nic,
                        'address': _self.address
                    }
                    inv_ids = inv_obj.create(cr, uid, inv_vals, context=context)
                    prices = config_obj.search(cr, uid, [('type', '=', type)])
                    for price in config_obj.browse(cr, uid, prices, context=context):
                        sp = price.price
                    inv_lines_vals = {
                        'name': inv_ids,
                        'products': _self.product_id.name,
                        'quantity': _self.product_qty,
                        'price_unit': sp,
                        'chassis_number': _self.chassis_number,
                        'engine_number': _self.engine_number,
                    }
                    inv_obj_line.create(cr, uid, inv_lines_vals, context=context)

        ir_model_data = self.pool.get('ir.model.data')
        form_res = ir_model_data.get_object_reference(cr, uid, 'custom_inventory', 'custom_dummy_invoice_form')
        form_id = form_res and form_res[1] or False
        tree_res = ir_model_data.get_object_reference(cr, uid, 'custom_inventory', 'custom_dummy_invoice_tree_view')
        tree_id = tree_res and tree_res[1] or False
        return {
            'name': _('Certificate Invoices'),
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'custom.dummy.invoice',
            'res_id': inv_ids,
            'view_id': False,
            'views': [(form_id, 'form'), (tree_id, 'tree')],
            'type': 'ir.actions.act_window',
        }


class custom_certificate_inv_config(osv.osv):
    _name = 'custom.cert.inv.config'
    _rec_name = 'type'
    _columns = {
        'type': fields.selection([('Registered', 'For Registered Customer'),
                                  ('Unregistered', 'For Unregistered Customer'),
                                  ('sara_to_abc', 'Sara To ABC'),
                                  ('dealer_abc', 'For Dealer ABC')]
                                 ,store=True,string='Type'),
        'price': fields.float('Price', store=True)
    }