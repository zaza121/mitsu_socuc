# -*- coding: utf-8 -*-
from odoo import api, fields, models, Command, _
from odoo.osv import expression
from odoo.exceptions import ValidationError
from datetime import datetime


class ProjectTempTask(models.Model):
    _name = 'mitsu_sale.project_temp_task'
    _description = "Project template task"

    name = fields.Char(string='Nom')
    project_temp_id = fields.Many2one(
        comodel_name='project.project',
        string='Project',
    )
    project_id = fields.Many2one(
        comodel_name='project.project',
        string='Project',
        ondelete='set null'
    )
    product_temp_ids = fields.Many2many(
        comodel_name='product.template',
        relation='product_2_projectpt',
        string='Produits',
    )
