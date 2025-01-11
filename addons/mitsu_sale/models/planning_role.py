# -*- coding: utf-8 -*-
from odoo import api, fields, models, Command, _
from odoo.osv import expression
from odoo.exceptions import ValidationError
from datetime import datetime


class Planning(models.Model):
    _inherit = 'planning.role'

    cost_ids = fields.One2many(
        comodel_name='mitsu_sale.cost_role_line',
        inverse_name='role_id',
        string='Lignes cout',
    )


class CostRoleLine(models.Model):
    _name = "mitsu_sale.cost_role_line"
    _description = "Cout du role"

    role_id = fields.Many2one(
        comodel_name='planning.role',
        string='Role',
    )
    uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Unite',
    )
    amount = fields.Float(string='Taux')
