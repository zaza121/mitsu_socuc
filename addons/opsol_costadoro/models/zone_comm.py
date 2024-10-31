# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ZoneComm(models.Model):
    _name = 'opsol_costadoro.zone_comm'

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Nom de la zone doit etre unique.'),
    ]

    archive = fields.Boolean(string='Archive')
    name = fields.Char(string='Nom')
    description = fields.Text(string='Description')
