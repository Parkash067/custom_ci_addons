from openerp import models, fields, api, _


class logo_invoice(models.Model):
    _name = "logo.invoice"

    type = fields.Selection([
        ('Sara Automobiles', 'Sara Automobiles'),
        ('Allied Business Corporation', 'Allied Business Corporation'),
    ], string='Type',
        track_visibility='always')
    logo = fields.Binary('Logo', store=True)