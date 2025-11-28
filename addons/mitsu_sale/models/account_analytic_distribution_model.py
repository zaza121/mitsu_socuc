# -*- coding: utf-8 -*-
from odoo import api, fields, models, Command, _
from odoo.osv import expression
from odoo.exceptions import ValidationError
from datetime import datetime


class AccountAnalyticDistributionModel(models.Model):
    _inherit = 'account.analytic.distribution.model'
    _rec_name = "name"

    name = fields.Char(string='Nom')
