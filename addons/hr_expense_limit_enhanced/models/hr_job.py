from odoo import models, fields

class HrJob(models.Model):
    _inherit = 'hr.job'

    expense_limit = fields.Float(string="Limite par ligne")
    max_sheet_total = fields.Float(string="Plafond total par feuille")
    expense_limit_tolerance = fields.Float(string="Tolérance de dépassement (%)", default=0.0)