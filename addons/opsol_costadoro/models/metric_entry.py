# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class MetricEntry(models.Model):
    _name = 'opsol_costadoro.metric_entry'
    _description = "Entree de de mesure"

    line_metric_id = fields.Many2one(
        comodel_name='opsol_costadoro.line_metric',
        string='Metric',
    )
    equipment_id = fields.Many2one(
        comodel_name='equipment.details',
        related="line_metric_id.equipment_id"
    )
    metric_id = fields.Many2one(
        comodel_name='opsol_costadoro.metrique_equip',
        string='Metric',
        related="line_metric_id.metric_id"
    )
    uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Unite de mesure',
        related="line_metric_id.uom_id"
    )
    use_hour = fields.Boolean(
        string='Use Hour',
        compute="compute_use_hour"
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Client',
        related="line_metric_id.partner_id"
    )
    serial_no = fields.Char(related="line_metric_id.serial_no")
    value = fields.Float(
        string='Value',
        compute="compute_value",
        store=True,
        readonly=False
    )
    date_start = fields.Datetime(string='Date Debut')
    date_end = fields.Datetime(string='Date Fin')
    note = fields.Text(string='Note')

    @api.depends("uom_id")
    def compute_use_hour(self):
        uom_hour = self.env.ref("uom.product_uom_hour")
        if not uom_hour:
            raise UserError(_("l'unite de mesure de base heure est manquante, veuillez svp corriger cette erreur."))
        for rec in self:
            rec.use_hour = rec.uom_id.id == uom_hour.id or False

    @api.depends("date_start", "date_end")
    def compute_value(self):
        for rec in self:
            value = 0
            if rec.use_hour and rec.date_start and rec.date_end:
                if rec.date_end < rec.date_start:
                    raise UserError(_("Date de debut ne peut pas etre apres date de fin"))
                diff = rec.date_end - rec.date_start
                value = diff.seconds / 3600.0
            rec.value = value
