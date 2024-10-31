# -*- coding: utf-8 -*-

from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.fields import Command


class EqAddentryWiz(models.TransientModel):

    _name = 'opsol_costadoro.eq_addentry_wiz'
    _description = "Add entry measure Equipment"

    equipment_id = fields.Many2one(
        comodel_name='equipment.details',
        string='Equipment',
    )
    line_metric_id = fields.Many2one(
        comodel_name='opsol_costadoro.line_metric',
        string='Line metric',
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
                value = diff.seconds / 3600.0 + diff.days * 24
            rec.value = value

    def add_entry(self):
        self.ensure_one()
        values = {
            'line_metric_id': self.line_metric_id.id,
            'value': self.value,
            'note': self.note,
            'date_start': self.date_start,
            'date_end': self.date_end,
        }
        self.env["opsol_costadoro.metric_entry"].create(values)
