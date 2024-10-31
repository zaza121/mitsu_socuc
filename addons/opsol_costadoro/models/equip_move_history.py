
from odoo import api, fields, models, Command, _
from odoo.addons.opsol_costadoro.models.equipment_details import COSTADORO_STATE
import logging
import functools


class EquipMoveHistory(models.Model):
    _name = "opsol_costadoro.equip_move_history"
    _description = "Moves history"

    date = fields.Date(string='Date', default=fields.Date.today())
    old_value = fields.Char(string='Ancienne Valeur')
    new_value = fields.Char(string='Nouvelle valeur')
    user_id = fields.Many2one(
        comodel_name="res.users",
        string='Utilisateur',
        default=lambda self: self.env.user.id
    )
    equip_id = fields.Many2one(
        comodel_name='equipment.details',
        string='Equipement',
    )


class EquipMoveHistoryLine(models.Model):
    _name = "opsol_costadoro.equip_mvhistory_line"
    _description = "Moves history Line"

    date = fields.Date(string='Date', default=fields.Date.today())
    partner_id = fields.Many2one(comodel_name='res.partner', string='Client')
    date_debut = fields.Date(string='Date de debut')
    date_fin = fields.Date(string='Date de fin')
    equip_id = fields.Many2one(
        comodel_name='equipment.details',
        string='Equipement',
    )
    cost_state = fields.Selection(
        string="State",
        required=True,
        selection=COSTADORO_STATE,
        readonly=False
    )
