# -*- coding: utf-8 -*-
from odoo import api, fields, models, Command, _
from odoo.osv import expression
from odoo.exceptions import ValidationError
from datetime import datetime


class HrEmployee(models.Model):
    _inherit = 'hr.department'

    equipe_ids = fields.Many2many(
        comodel_name='mitsu_hr.equipe',
        string='Equipes',
        relation="equipe_to_depart"
    )
