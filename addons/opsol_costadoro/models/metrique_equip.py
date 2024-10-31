# -*- coding: utf-8 -*-

from odoo import api, fields, models


class MetriqueEquip(models.Model):
    _name = 'opsol_costadoro.metrique_equip'
    _description = "Type de metrique"

    name = fields.Char(string='Name')
    uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='unite de mesure',
    )
    description = fields.Text(string='Description')
