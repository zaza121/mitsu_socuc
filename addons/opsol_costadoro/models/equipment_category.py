# -*- coding: utf-8 -*-
from odoo import api, fields, models


class EquipmentCategory(models.Model):
    _inherit = 'equipment.category'
    _parent_name = "parent_id"
    _parent_store = True

    parent_id = fields.Many2one(
        comodel_name='equipment.category',
        string='Parent',
        index=True, ondelete='cascade'
    )
    parent_path = fields.Char(index=True, unaccent=False)
