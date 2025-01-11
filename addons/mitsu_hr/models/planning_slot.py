# -*- coding: utf-8 -*-
from odoo import api, fields, models, Command, _
from odoo.osv import expression
from odoo.exceptions import ValidationError
from datetime import datetime


class Planning(models.Model):
    _inherit = 'planning.slot'

    manager_ids = fields.Many2many(
        comodel_name='res.users',
        string='Resources',
        compute="compute_manager_ids",
        store=True
    )

    @api.depends("employee_id.equipe_ids.manager_id")
    def compute_manager_ids(self):
        for rec in self:
            rec.manager_ids = rec.mapped("employee_id.equipe_ids.manager_id")
