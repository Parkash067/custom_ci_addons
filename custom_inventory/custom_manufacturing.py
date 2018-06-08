import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv
from openerp import api, _


class custom_manufacturing_stages(osv.osv):
    _name = 'custom.production.stages'
    _rec_name = 'name'
    _columns = {
        'name': fields.char('Stage Name', store=True),
        'state': fields.char('State Name', store=True),
        'sequence': fields.integer('Sequence', store=True)
    }


class custom_manufacturing(osv.osv):
    _inherit = 'mrp.production'
    _columns = {
        'location_src_id': fields.many2one('stock.location', 'Raw Materials Location', required=True,
                                           readonly=False,
                                           help="Location where the system will look for components."),
        'location_dest_id': fields.many2one('stock.location', 'Finished Products Location', required=True,
                                            readonly=False,
                                            help="Location where the system will stock the finished products."),
        'stage': fields.many2one('custom.production.stages', 'Stage', store=True, compute='assign_stage')

    }

    @api.depends('state')
    def assign_stage(self):
        stage = self.env['custom.production.stages'].search([['state', '=', self.state], ])
        self.stage = stage
        return True


class custom_mrp_product_produce(osv.osv_memory):
    _inherit = 'mrp.product.produce'
    _columns = {
        'production_lines': fields.one2many('custom.produce', 'name', 'Production Lines')
    }

    @api.multi
    def wizard_view(self):
        view = self.env.ref('custom_inventory.custom_production_lines')

        return {
            'name': _('Enter transfer details'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mrp.product.produce',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.ids[0],
            'context': self.env.context,
        }

    @api.multi
    def split_quantities(self):
        for det in self.production_lines:
            if det.product_qty > 1:
                det.product_qty = (det.product_qty - 1)
                new_id = det.copy(context=self.env.context)
                new_id.product_qty = 1
                self.split_quantities()
        if self.production_lines and self.production_lines[0]:
            return self.production_lines[0].name.wizard_view()

    def default_get(self, cr, uid, fields, context=None):
        if context is None: context = {}
        res = super(custom_mrp_product_produce, self).default_get(cr, uid, fields, context=context)
        mrp_ids = context.get('active_ids', [])
        active_model = context.get('active_model')

        if not mrp_ids or len(mrp_ids) != 1:
            # Partial Picking Processing may only be done for one picking at a time
            return res
        assert active_model in ('mrp.production'), 'Bad context propagation'
        mrp_id, = mrp_ids
        mrp = self.pool.get('mrp.production').browse(cr, uid, mrp_id, context=context)
        items = []
        for op in mrp.move_created_ids:
            item = {
                'product_qty': op.product_uom_qty,
                'engine_number': 'SAE-',
                'chassis_number': 'SAC-',
                'mode':'consume_produce'
            }
            if op.product_id:
                items.append(item)
        res.update(production_lines=items)
        return res

    def do_produce(self, cr, uid, ids, context=None):
        stock_production_lot = self.pool.get('stock.production.lot')
        production_id = context.get('active_id', False)
        cr.execute("""select product_id from mrp_production where id=%s""" % (production_id))
        product_id = cr.dictfetchall()[0]['product_id']
        assert production_id, "Production Id should be specified in context as a Active ID."
        data = self.browse(cr, uid, ids[0], context=context)
        for line in data.production_lines:
            self.pool.get('mrp.production').action_produce(cr, uid, production_id,
                                                           line.product_qty, line.mode, data, context=context)
            rec_id = stock_production_lot.create(cr, uid, {'name': line.engine_number,
                                                           'chassis_number': line.chassis_number,
                                                           'color': line.color,
                                                           'model': line.model,
                                                           'year': line.year,
                                                           'product_id': product_id
                                                           }, context=context)
        return {}


class custom_produce(osv.osv_memory):
    _name = 'custom.produce'
    _rec_name = 'engine_number'
    _columns = {
        'name': fields.many2one('mrp.product.produce', string='Name'),
        'mode': fields.selection([('consume_produce', 'Consume & Produce'),
                                  ('consume', 'Consume Only')], string='Mode',required=True, default='consume_produce'),
        'product_id': fields.many2one('product.template', string='Product'),
        'product_qty': fields.float('Quantity',required=True),
        'engine_number': fields.char('Engine Number', default='SAE-'),
        'chassis_number': fields.char('Chassis Number', default='SAC-'),
        'color': fields.selection([('Black', 'Black'),
                                   ('Red', 'Red'),
                                   ('Blue', 'Blue'),
                                   ('Silver', 'Silver'),
                                   ('Yellow', 'Yellow'),
                                   ], string='Color'),
        'model': fields.char('Model', ),
        'year': fields.selection([('2010', '2010'), ('2011', '2011'), ('2012', '2012'), ('2013', '2013'),
                                  ('2014', '2014'), ('2015', '2015'), ('2016', '2016'), ('2017', '2017'),
                                  ('2018', '2018'), ('2019', '2019'), ('2020', '2020'), ('2021', '2021'),
                                  ('2022', '2022'), ('2023', '2023'), ('2024', '2024'), ('2025', '2025'),
                                  ('2026', '2026'),
                                  ('2027', '2027'),
                                  ], string='Year', store=True,),
    }
    

    @api.multi
    def split_quantities(self):
        for det in self:
            if det.quantity > 1:
                det.quantity = (det.quantity - 1)
                new_id = det.copy(context=self.env.context)
                new_id.quantity = 1
                new_id.packop_id = False
        if self and self[0]:
            return self[0].transfer_id.wizard_view()
