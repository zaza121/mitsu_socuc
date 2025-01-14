import logging
from odoo import api, fields, models, _

REGION = [
    ('littoral', 'Littoral'),
    ('adamawa', 'Adamawa'),
    ('centtre', 'Centre'),
    ('east', 'East'),
    ('far_north', 'Far north'),
    ('north', 'North'),
    ('north_west', 'North west'),
    ('south', 'South'),
    ('south', 'South west'),
    ('west', 'West'),

]

class ResCity(models.Model):
    _name = "res.city"
    name = fields.Char('Ville de destination', required=True, index=True)
    zipcode = fields.Char('Zip code', index=True)
    country_id = fields.Many2one('res.country', require=True,
        domain = [('phone_code', '=' , 237)]
        )
    region = fields.Selection(REGION, _("Region"), default='littoral')