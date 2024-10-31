
from odoo import api, fields, models, Command, _
import logging
import functools

LABEL_RUBRIQUE = {
    'mepa': 'ME Parts','meot': 'ME Others',
    'gspa': 'GS Parts', 'gsot': 'GS Others',
    'gbpa': 'GB Parts', 'gbot': 'GB Others',
    'gsadpa': 'Supply Parts', 'gsadot': 'GS AD Others'}


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    rubrique = fields.Selection(
        name="Rubrique",
        selection=[
            ('mepa', 'ME Parts'), ('meot', 'ME Others'),
            ('gspa', 'GS Parts'), ('gsot', 'GS Others'),
            ('gbpa', 'GB Parts'), ('gbot', 'GB Others'),
            ('gsadpa', 'GSAD Parts'), ('gsadot', 'GSAD Others')
        ]
    )
