from openerp import models, fields, api, _
from openerp.osv import fields, osv
from datetime import datetime
from openerp.exceptions import ValidationError


class custom_stock_serial(osv.osv):
    _inherit = 'stock.production.lot'
    _columns = {
        'company': fields.related('product_id', 'company_id', relation="res.company", type='many2one',
                                       string="Company", store=True),
        'status': fields.selection([('Available', 'Available'),
                                    ('Issued', 'Issued')], string='Status', store=True),
        'chassis_number': fields.char('Chassis No.', store=True),
        'color': fields.char('Color', store=True, compute='fetch_color'),
        'model': fields.char(string='Model', store=True),
        'year': fields.selection([('2010', '2010'), ('2011', '2011'), ('2012', '2012'), ('2013', '2013'),
                                  ('2014', '2014'), ('2015', '2015'), ('2016', '2016'), ('2017', '2017'),
                                  ('2018', '2018'), ('2019', '2019'), ('2020', '2020'), ('2021', '2021'),
                                  ('2022', '2022'), ('2023', '2023'), ('2024', '2024'), ('2025', '2025'),
                                  ('2026', '2026'),
                                  ('2027', '2027'),
                                  ], string='Year', store=True),
    }

    _defaults = {
        'status': 'Available',
        'name': 'SAE-',
        'chassis_number': 'SAC-',
        'model': '70 CC',
        'year': '2018'
    }

    @api.constrains('name')
    def _check_unique_constraint(self):
        if len(self.search([('name', '=', self.name),('company', '=', self.company.id)])) > 1:
            raise ValidationError("This engine number already exists and violates unique field constraint")

    @api.constrains('chassis_number')
    def _check_unique_constraint_(self):
        if len(self.search([('name', '=', self.name),('company', '=', self.company.id)])) > 1:
            raise ValidationError("This chassis number already exists and violates unique field constraint")

    @api.one
    @api.depends('product_id')
    def fetch_color(self):
        products = [1856, 1850, 1851, 1852, 1853, 1854, 1855, 1857, 1858,
                    1862, 1980, 1981, 1982, 1983, 1984, 1985, 1986, 1987]
        if self.product_id and self.product_id.id in products:
            color = ''
            attribute = (self.product_id.attribute_value_ids[0].name).split(' ')
            if attribute[0] == 'Durbi' or attribute[0] == 'Smart' or attribute[0] == 'Self':
                for _color in attribute:
                    color += _color + " "
            self.color = color