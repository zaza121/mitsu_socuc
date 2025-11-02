# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Ressource',
    )

    @api.onchange('planning_role_id')
    def _onchange_planning_role_id(self):
        # si on change le rôle de planning, on réinitialise la ressource
        self.employee_id = None

    @api.onchange('employee_id')
    def _onchange_employee_id_set_price(self):
        # quand on choisit une ressource, on positionne le prix de vente sur le coût horaire
        if self.employee_id and hasattr(self.employee_id, 'hourly_cost'):
            # safe fallback : si hourly_cost est False/None => 0.0
            self.list_price = self.employee_id.hourly_cost or 0.0
        else:
            # si pas de ressource, on ne modifie pas ou on met 0
            self.list_price = self.list_price or 0.0
