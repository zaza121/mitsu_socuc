# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PlanningSlot(models.Model):
    _inherit = 'planning.slot'

    manager_ids = fields.Many2many(
        comodel_name='res.users',
        string='Managers d\'équipe',
        compute="_compute_manager_ids",
        store=True
    )

    @api.depends("employee_id.equipe_ids.manager_id")
    def _compute_manager_ids(self):
        for rec in self:
            # prend les managers des équipes auxquelles appartient l'employé
            rec.manager_ids = rec.employee_id and rec.employee_id.equipe_ids.mapped('manager_id') or self.env['res.users']
