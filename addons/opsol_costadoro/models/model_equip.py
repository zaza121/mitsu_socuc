# -*- coding: utf-8 -*-
from odoo import models, fields, api, Command, _
from odoo.exceptions import UserError
from datetime import date


class ModelEquip(models.Model):
    _name = 'opsol_costadoro.model_equip'

    name = fields.Char(string='Nom')
    description = fields.Char(string='Description')
