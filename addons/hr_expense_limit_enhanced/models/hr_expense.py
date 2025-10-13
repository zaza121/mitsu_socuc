from odoo import models, fields

class HrExpense(models.Model):
    _inherit = 'hr.expense'

    justification_text = fields.Text(string="Justification", help="Motif à remplir si la dépense dépasse la limite autorisée.")