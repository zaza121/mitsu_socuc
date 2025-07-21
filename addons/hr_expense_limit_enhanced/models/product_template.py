from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    expense_limit = fields.Float(
        string="Limite de dépense",
        help="Montant maximum autorisé pour cette catégorie de dépense."
    )