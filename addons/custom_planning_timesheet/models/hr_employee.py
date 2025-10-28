from odoo import models, fields

class HREmployee(models.Model):
_inherit = 'hr.employee'

role_ids = fields.Many2many('hr.job', string="Rôles possibles")