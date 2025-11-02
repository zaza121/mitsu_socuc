# -*- coding: utf-8 -*-
from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    equipe_ids = fields.Many2many(
        comodel_name='mitsu_hr.equipe',
        string='Équipes',
        relation="equipe_to_emp"
    )
