# -*- coding: utf-8 -*-

from odoo import api, fields, models

class StockMove(models.Model):
    _inherit = 'stock.move'

    equipments_ids = fields.Many2many(
        comodel_name='equipment.details',
        relation="move_to_equip",
        string='Equipments',
    )
    out_move_sign = fields.Float(
        string="Out Move Sign",
        compute="compute_out_move_sign",
        store=True,
    )

    @api.depends("location_id", "location_dest_id")
    def compute_out_move_sign(self):
        for rec in self:
            if rec.location_id.id == rec.location_dest_id:
                rec.out_move_sign = 0
            elif rec.location_dest_id.usage == "customer":
                rec.out_move_sign = 1
            elif rec.location_id.usage == "customer":
                rec.out_move_sign = -1
            else:
                rec.out_move_sign = 0
    
    def create_metric_line(self):
        self = self.filtered(lambda x: x.product_id and x.product_id.metrics_ids)
        for rec in self:
            lines = self.env["opsol_costadoro.line_metric"].search([
                ('partner_id', '=', rec.picking_id.partner_id.id),('metric_id', 'in', rec.product_id.metrics_ids.ids)])
            for mequip in lines:
                values = {
                    'line_metric_id': mequip.id,
                    'value': rec.product_uom_qty,
                    'note': rec.picking_id.name,
                    'date_start': None,
                    'date_end': None,
                }
                self.env["opsol_costadoro.metric_entry"].create(values)
                rec.equipments_ids |= mequip.equipment_id
