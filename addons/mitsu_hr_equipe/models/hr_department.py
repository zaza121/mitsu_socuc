# -*- coding: utf-8 -*-
from odoo import fields, models


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    equipe_ids = fields.Many2many(
        comodel_name='mitsu_hr.equipe',
        string='Équipes',
        relation="equipe_to_depart"
    )
