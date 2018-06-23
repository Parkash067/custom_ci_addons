from openerp import models,fields,api,_
from openerp.osv import fields,osv
from datetime import datetime
from openerp.exceptions import ValidationError

class custom_stock_serial(osv.osv):
    _inherit = 'stock.production.lot'
    _columns = {
        'status': fields.selection([('Available','Available'),
                                    ('Issued','Issued')],string='Status', store=True),
        'chassis_number': fields.char('Chassis No.', store=True),
        'color': fields.selection([('Black','Black'),
                                   ('Red', 'Red'),
                                   ('Blue', 'Blue'),
                                   ('Silver', 'Silver'),
                                   ('Yellow', 'Yellow'),
                                   ],string='Color',store=True),
        'model': fields.char(string='Model',store=True),
        'year': fields.selection([('2010','2010'),('2011', '2011'),('2012', '2012'),('2013', '2013'),
                                   ('2014', '2014'),('2015', '2015'),('2016', '2016'),('2017', '2017'),
                                   ('2018','2018'),('2019', '2019'),('2020', '2020'),('2021', '2021'),
                                   ('2022', '2022'),('2023', '2023'),('2024', '2024'),('2025', '2025'),
                                   ('2026', '2026'),
                                   ('2027', '2027'),
                                   ],string='Year',store=True),
    }

    _defaults = {
        'status': 'Available',
        'name': 'SAE-',
        'chassis_number': 'SAC-',
    }

    @api.constrains('name')
    def _check_unique_constraint(self):
        if len(self.search([('name', '=', self.name),])) > 1:
            raise ValidationError("This engine number already exists and violates unique field constraint")

    @api.constrains('chassis_number')
    def _check_unique_constraint(self):
        if len(self.search([('chassis_number', '=', self.chassis_number), ])) > 1:
            raise ValidationError("This chassis number already exists and violates unique field constraint")