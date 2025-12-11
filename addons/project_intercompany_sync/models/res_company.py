from odoo import fields, models

class ResCompany(models.Model):
    _inherit = 'res.company'
    
    is_subcontractor = fields.Boolean(
        string="Est sous-traitante",
        help="Cochez cette case si cette société peut être sélectionnée comme société miroir dans les tâches inter-sociétés."
    )