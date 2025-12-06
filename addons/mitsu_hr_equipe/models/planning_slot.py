
from odoo import models, fields, api

class PlanningSlot(models.Model):
    _inherit = 'planning.slot'

    employee_team_id = fields.Many2one('hr.employee.team', string='Équipe', compute='_compute_employee_team_id', store=True)

    @api.depends('employee_id.team_ids')
    def _compute_employee_team_id(self):
        for slot in self:
            slot.employee_team_id = slot.employee_id.team_ids[:1].id if slot.employee_id and slot.employee_id.team_ids else False
