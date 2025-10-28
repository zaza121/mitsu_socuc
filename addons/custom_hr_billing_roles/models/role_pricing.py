from odoo import models, fields

class RolePricing(models.Model):
_name = 'role.pricing'
_description = 'Grille tarifaire par Rôle et Unité'

role_id = fields.Many2one('hr.job', string="Rôle", required=True)
uom_id = fields.Many2one('uom.uom', string="Unité de Mesure", required=True)
price = fields.Float(string="Prix de Vente Unitaire", required=True)
company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Devise", readonly=True)