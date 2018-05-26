# -*- coding: utf-8 -*-
#################################################################################
#
#    Copyright (c) 2015-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#
#################################################################################
from openerp.osv import fields, osv
from openerp import models, fields, api, _


class res_partner(osv.osv):
    _inherit = "res.partner"

    taxation = fields.Selection([('Tax Payer','Tax Payer'),('Non Tax Payer','Non Tax Payer')], default='Non Tax Payer', String='Tax Condition', required=True)
    ntn = fields.Char(string="NTN", domain=[('taxation','=','n-pay')])
    nic = fields.Char(string="NIC")
    strn = fields.Char(string="STRN")
    gst = fields.Char(string="GST")
    city_id = fields.Many2one('res.city', string="City", required=True)
    region_id = fields.Many2one('res.region', string="Region", required=True)
    custom_type = fields.Selection([('department','WH Department')], 'Type', store=True)

# class stock_picking(osv.osv):
#     _inherit = "stock.picking"
#
#     deliver_to = fields.Many2one('res.partner', String="Deliver To", states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
#     contact_to = fields.Char(string="Contact Info", states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
#     contact_nic = fields.Char(string="Customer N.I.C", states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
#     transporter = fields.Char(string="Transporter", states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
#     driver = fields.Char(string="Driver Name", states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
#     vehicle = fields.Char(string="Vehicle No.", states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
#     contact_no = fields.Char(string="Phone No.", states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
#
class res_city(models.Model):
    _name = "res.city"
    _description = "Cities"
    _order = "name"

    name = fields.Char(string="City Name", required=True)
    code = fields.Char(string="Code")
    state = fields.Many2one('res.country.state', string="State", required=True)
#
class res_region(models.Model):
    _name = "res.region"
    _description = "Regions"
    _order = "name"

    name = fields.Char(string="Region Name", required=True)
    code = fields.Char(string="Code")
    city = fields.Many2one('res.city', string="City", required=True)
#
# class res_color(models.Model):
#     _name = "res.color"
#     _description = "Colors"
#     _order = "name"
#
#     name = fields.Char(string="Color Name", required=True)
#     code = fields.Char(string="Code")
#
# class res_model(models.Model):
#     _name = "res.model"
#     _description = "Models Name"
#     _order = "name"
#
#     name = fields.Char(string="Model Name", required=True)
#     code = fields.Char(string="Code")
#
# class res_year(models.Model):
#     _name = "res.year"
#     _description = "Models Years"
#     _order = "name"
#
#     name = fields.Char(string="Model Name", required=True)
#     code = fields.Char(string="Code")
#     start_date = fields.Datetime(string="Start Date", required=True)
#     end_date = fields.Datetime(string="End Date", required=True)
#
# class stock_production_lot(osv.osv):
#     _inherit = "stock.production.lot"
#
#     color_id = fields.Many2one('res.color', String='Color', readonly=True)
#     model_id = fields.Many2one('res.model', String='Model', readonly=True)
#     year_id = fields.Many2one('res.year', string="Year", readonly=True)
#
# class stock_pack_operation(osv.osv):
#     _inherit = "stock.pack.operation"
#
#     color_id = fields.Many2one('res.color', String='Color', default= 1)
#     model_id = fields.Many2one('res.model', String='Model', default= 1)
#     year_id = fields.Many2one('res.year', string="Year", default= 1)
#     ref = fields.Char('Engine No.', default='SAE-', required=False)
#
#     _sql_constraints = [
# 		('lot_id_uniq','unique(lot_id)',_("Chessis Number Already Dispatched !")),
# 		 ]
#
# class stock_transfer_details_items(osv.osv):
#     _inherit = "stock.transfer_details_items"
#
#     color_id = fields.Many2one('res.color', String='Color')
#     model_id = fields.Many2one('res.model', String='Model')
#     year_id = fields.Many2one('res.year', string="Year")
#     ref = fields.Char('Engine No.', default='SAE-')
