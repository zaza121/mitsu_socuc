# -*- coding: utf-8 -*-
from odoo import api, fields, models, Command, _
from odoo.osv import expression
from odoo.exceptions import ValidationError
from datetime import datetime


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Resource',
    )

    @api.onchange('planning_role_id')
    def _onchange_planning_role_id(self):
        self.employee_id = None

    @api.constrains('employee_id')
    def get_hourly_cost(self):
        for rec in self:
            rec.list_price = rec.employee_id and rec.employee_id.hourly_cost or 0
