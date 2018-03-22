import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv
from openerp import api,_


class custom_manufacturing_stages(osv.osv):
    _name = 'custom.production.stages'
    _rec_name = 'name'
    _columns = {
        'name': fields.char('Stage Name',store=True),
        'state': fields.char('State Name', store=True),
        'sequence': fields.integer('Sequence', store=True)
    }


class custom_manufacturing(osv.osv):
    _inherit = 'mrp.production'
    _columns = {
        'stage': fields.many2one('custom.production.stages', 'Stage', store=True, compute='assign_stage')

    }

    @api.depends('state')
    def assign_stage(self):
        stage = self.env['custom.production.stages'].search([['state', '=', self.state], ])
        self.stage = stage
        return True

