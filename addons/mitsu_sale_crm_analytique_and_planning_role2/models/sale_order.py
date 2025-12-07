# -*- coding: utf-8 -*-
from odoo import api, fields, models, Command, _
from odoo.osv import expression
from odoo.exceptions import ValidationError
from datetime import datetime


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    force_distribution_id = fields.Many2one(
        comodel_name='account.analytic.distribution.model',
        string='Force Modele analytique',
    )
