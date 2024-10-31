# -*- coding: utf-8 -*-
import re

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_cafe = fields.Boolean(string='Est un cafe ?', default=False)
    metrics_ids = fields.Many2many(
        comodel_name='opsol_costadoro.metrique_equip',
        string='Metriques de l\'article',
    )
