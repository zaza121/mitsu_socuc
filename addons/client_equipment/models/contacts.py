
from odoo import api, models, fields

class ResPartner(models.Model):
    _inherit = "res.partner"


    site_contact = fields.Char(string="Site Contact")

    site_phone = fields.Char(string="Site Phone")




