import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv
from openerp import api,_


class custom_debit_note(osv.osv):
    _name = 'custom.debit.note'
    _rec_name = 'name'
    _columns = {
        'type': fields.selection([('Debit Note','Debit Note'),('Credit Note','Credit Note')],store=True,string='Note Type'),
        'view_invoice_id': fields.integer('View ID', store=True),
        'view_id': fields.integer('View ID', store=True),
        'name': fields.char('Name', store=True),
        'partner_id': fields.many2one('res.partner','Supplier/Customer', store=True, duplicate=True, domain="['|',('supplier','=',True),('customer','=',True)]"),
        'supplier_invoice': fields.many2one('account.invoice', 'Supplier Invoice', store=True, duplicate=True),
        'date': fields.date('Date', store=True, duplicate=True),
        'debit_note_line': fields.one2many('custom.debit.note.line', 'name', 'Debit Note Lines', store=True),
        'amount_untaxed': fields.float('Subtotal', store=True, readonly=True, default=0.0,
                                       compute='cal_tax_and_untaxedamount'),
        'amount_tax': fields.float('Sales Tax', store=True, readonly=True, default=0.0,
                                   compute='cal_tax_and_untaxedamount'),
        'amount_total': fields.float('Total', store=True, readonly=True, default=0.0, compute='cal_total_amount'),
        'comment': fields.text('Comment', store=True),
        'status': fields.selection([('draft', 'Draft'),
                                    ('inventory_adjustment', 'Inventory Adjustment'),
                                    ('invoice_adjustment', 'Invoice Adjustment')], string='State', store=True),
    }

    _defaults = {
        'status': 'draft',
        'name': '/'
    }

    def create(self, cr, uid, vals, context=None):
        vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'debit_note.serial')
        return super(custom_debit_note, self).create(cr, uid, vals, context=context)

    @api.onchange('type')
    def change_domain(self):
        if self.type == 'Credit Note':
            return {'domain': {'partner_id': [('customer', '=', True)]}}

        if self.type == 'Debit Note':
            return {'domain': {'partner_id': [('supplier', '=', True)]}}

    def view_order(self, cr, uid, ids, context=None):
        _self = self.browse(cr, uid, ids[0], context=context)
        ir_model_data = self.pool.get('ir.model.data')
        form_res = ir_model_data.get_object_reference(cr, uid, 'custom_inventory', 'claim_return_form_view')
        form_id = form_res and form_res[1] or False
        tree_res = ir_model_data.get_object_reference(cr, uid, 'custom_inventory', 'claim_return_tree_view')
        tree_id = tree_res and tree_res[1] or False
        return {
            'name': _('Debit Note'),
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'stock.picking',
            'res_id': _self.view_id,
            'view_id': False,
            'views': [(form_id, 'form'), (tree_id, 'tree')],
            'type': 'ir.actions.act_window',
        }

    def deduct_inventory(self, cr, uid, ids, context=None):
        stock_location_obj = 0
        picking_id = 0
        stock_location_dest_obj = 0
        _self = self.browse(cr, uid, ids[0], context=context)
        debit_note_lines = {}
        if _self.type == 'Debit Note':
            stock_wh_obj = self.pool.get('stock.warehouse').search(cr, uid, [('name', '=', 'Sara Automobiles')])
            stock_location_obj = self.pool.get('stock.location').search(cr, uid, [('name', '=', 'Stock')])
            stock_location_dest_obj = self.pool.get('stock.location').search(cr, uid, [('name', '=', 'Suppliers')])
            picking_id = self.pool.get('stock.picking.type').search(cr, uid, [['name', '=', 'Delivery Orders'], ['warehouse_id', '=', stock_wh_obj[0]]])

        elif _self.type == 'Credit Note':
            stock_wh_obj = self.pool.get('stock.warehouse').search(cr, uid, [('name', '=', 'Sara Automobiles')])
            stock_location_obj = self.pool.get('stock.location').search(cr, uid, [('name', '=', 'Customers')])
            stock_location_dest_obj = self.pool.get('stock.location').search(cr, uid, [('name', '=', 'Stock')])
            picking_id = self.pool.get('stock.picking.type').search(cr, uid, [['name', '=', 'Receipts'],
                                                                      ['warehouse_id', '=', stock_wh_obj[0]]])

        stock_picking_obj = self.pool.get('stock.picking')
        stock_move_obj = self.pool.get('stock.move')
        debit_note_vals = {
            'partner_id': _self.partner_id.id,
            'picking_type_id': picking_id[0],
        }
        stock_id = stock_picking_obj.create(cr, uid, debit_note_vals, context=context)
        _self.view_id = stock_id
        for debit_note_line in _self.debit_note_line:
            debit_note_lines = {
                'name': debit_note_line.product_id.name,
                'picking_id': stock_id,
                'product_id': debit_note_line.product_id.id,
                'product_uom_qty': debit_note_line.quantity,
                'product_uom': debit_note_line.product_id.uom_id.id,
                'location_id':stock_location_obj[0],
                'location_dest_id':stock_location_dest_obj[0]
            }
        stock_move_obj.create(cr, uid, debit_note_lines, context=context)
        ir_model_data = self.pool.get('ir.model.data')
        form_res = ir_model_data.get_object_reference(cr, uid, 'custom_inventory', 'claim_return_form_view')
        form_id = form_res and form_res[1] or False
        tree_res = ir_model_data.get_object_reference(cr, uid, 'custom_inventory', 'claim_return_tree_view')
        tree_id = tree_res and tree_res[1] or False
        _self.write({'status':'inventory_adjustment'})
        return {
            'name': _('Debit Note'),
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'stock.picking',
            'res_id': stock_id,
            'view_id': False,
            'views': [(form_id, 'form'), (tree_id, 'tree')],
            'type': 'ir.actions.act_window',
        }

    def view_invoice(self,cr, uid, ids, context=None):
        _self = self.browse(cr, uid, ids[0], context=context)
        ir_model_data = self.pool.get('ir.model.data')
        form_res = ir_model_data.get_object_reference(cr, uid, 'account', 'invoice_supplier_form')
        form_id = form_res and form_res[1] or False
        tree_res = ir_model_data.get_object_reference(cr, uid, 'account', 'invoice_tree')
        tree_id = tree_res and tree_res[1] or False
        return {
            'name': _('Supplier Returns'),
            'view_type': 'form',
            'view_mode': 'form,tree',
            'res_model': 'account.invoice',
            'res_id': _self.view_invoice_id,
            'view_id': False,
            'views': [(form_id, 'form'), (tree_id, 'tree')],
            'type': 'ir.actions.act_window',
        }

    def refund_invoice(self, cr, uid, ids, context=None):
        inv_vals_id = 0
        account_invoice_obj = self.pool.get('account.invoice')
        account_invoice_line_obj = self.pool.get('account.invoice.line')
        _self = self.browse(cr, uid, ids[0], context=context)
        inv_val_lines = {}
        if _self.type == 'Debit Note':
            account_journal_obj = self.pool.get('account.journal').search(cr, uid,
                                                                          [('name', '=', 'Purchase Refund Journal')])
            inv_vals = {
                'partner_id': _self.partner_id.id,
                'journal_id': account_journal_obj[0],
                'company_id': _self.partner_id.company_id.id,
                'account_id': _self.partner_id.property_account_payable.id,
                'type': 'in_refund'
            }
            inv_vals_id = account_invoice_obj.create(cr, uid, inv_vals, context=context)
        elif _self.type == 'Credit Note':
            account_journal_obj = self.pool.get('account.journal').search(cr, uid,[('name', '=', 'Sales Refund Journal')])
            inv_vals = {
                'partner_id': _self.partner_id.id,
                'journal_id': account_journal_obj[0],
                'company_id': _self.partner_id.company_id.id,
                'account_id': _self.partner_id.property_account_receivable.id,
                'type': 'out_refund'
            }
            inv_vals_id = account_invoice_obj.create(cr, uid, inv_vals, context=context)
        _self.view_invoice_id = inv_vals_id
        for line in _self.debit_note_line:
            inv_val_lines = {
                'invoice_id': inv_vals_id,
                'product_id':line.product_id.id,
                'name': line.product_id.name,
                'quantity': line.quantity,
                'uom_id':line.product_id.uom_id.id,
                'price_unit':line.price_unit,
            }
            account_invoice_line_obj.create(cr,uid, inv_val_lines,context=context)
        ir_model_data = self.pool.get('ir.model.data')
        if _self.type == 'Debit Note':
            form_res = ir_model_data.get_object_reference(cr, uid, 'account', 'invoice_supplier_form')
            form_id = form_res and form_res[1] or False
            tree_res = ir_model_data.get_object_reference(cr, uid, 'account', 'invoice_tree')
            tree_id = tree_res and tree_res[1] or False
            _self.write({'status': 'invoice_adjustment'})
            return {
                'name': _('Supplier Returns'),
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'account.invoice',
                'res_id': inv_vals_id,
                'view_id': False,
                'views': [(form_id, 'form'), (tree_id, 'tree')],
                'type': 'ir.actions.act_window',
            }
        else:
            form_res = ir_model_data.get_object_reference(cr, uid, 'account', 'invoice_form')
            form_id = form_res and form_res[1] or False
            tree_res = ir_model_data.get_object_reference(cr, uid, 'account', 'invoice_tree')
            tree_id = tree_res and tree_res[1] or False
            _self.write({'status': 'invoice_adjustment'})
            return {
                'name': _('Customer Returns'),
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'account.invoice',
                'res_id': inv_vals_id,
                'view_id': False,
                'views': [(form_id, 'form'), (tree_id, 'tree')],
                'type': 'ir.actions.act_window',
            }


    @api.one
    @api.depends('amount_untaxed', 'amount_tax')
    def cal_total_amount(self):
        self.amount_total = self.amount_tax + self.amount_untaxed
        return True

    @api.one
    @api.depends('debit_note_line.price_subtotal')
    def cal_tax_and_untaxedamount(self):
        for line in self.debit_note_line:
            self.amount_untaxed += line.price_subtotal
            self.amount_tax += line.sales_tax
        return True


class custom_debit_note_lines(osv.osv):
    _name = "custom.debit.note.line"
    _rec_name = 'name'
    _columns = {
        'name': fields.many2one('custom.debit.note','Name', store=True),
        'incl_val': fields.float('Incl. S.T Amount', store=True, compute='basic_amount'),
        'product_id': fields.many2one('product.product', 'Product', store=True),
        'quantity': fields.float('Quantity', store=True, default=0.0),
        'price_unit': fields.float('Unit Price', store=True, default=0.0),
        'sales_tax': fields.float('Sales Tax', store=True, default=0.0),
        'price_subtotal': fields.float('Excl. S.T Amount', store=True, readonly=True, default=0.0, compute='basic_amount'),
    }

    @api.one
    @api.depends('quantity', 'price_unit')
    def basic_amount(self):
        self.price_subtotal = self.quantity * self.price_unit
        self.incl_val = (self.quantity * self.price_unit) + self.sales_tax
        return True




