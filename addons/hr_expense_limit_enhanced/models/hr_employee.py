from odoo import models, fields

class HREmployee(models.Model):
    _inherit = 'hr.employee'

    monthly_expense_limit = fields.Float(
        string="Plafond mensuel de dépenses",
        help="Montant maximum total des dépenses validées sur un mois."
    )