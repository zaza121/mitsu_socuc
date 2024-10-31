# -*- coding: utf-8 -*-

from odoo import api, fields, models


class JourSemaine(models.Model):
    _name = 'opsol_costadoro.jour_semaine'
    _description = "Jour de la semaine"

    name = fields.Char(string='Name')
