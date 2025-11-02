from odoo import models, fields

class ResCompany(models.Model):
    _inherit = "res.company"

    is_subcontractor = fields.Boolean(
        string="Société sous-traitante",
        help="Indique si cette société peut être utilisée comme société miroir inter-sociétés.",
        default=False,
    )
