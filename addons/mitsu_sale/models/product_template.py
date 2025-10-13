# -*- coding: utf-8 -*-
from odoo import api, fields, models, Command, _
from odoo.osv import expression
from odoo.exceptions import ValidationError
from datetime import datetime


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    temp_task_ids = fields.Many2many(
        comodel_name='mitsu_sale.project_temp_task',
        relation='product_2_projectpt',
        string='Projet taches',
    )
