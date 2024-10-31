# -*- coding: utf-8 -*-
from odoo import models, fields, api, Command, _
from datetime import datetime, timedelta


class LineMetric(models.Model):
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _name = 'opsol_costadoro.line_metric'
    _description = "Metrique d equipement"
    _rec_name = 'name'

    name = fields.Char(
        string='Nom',
        compute="compute_name",
        store=True,
    )
    equipment_id = fields.Many2one(
        comodel_name='equipment.details',
        string='Equipment',
    )
    metric_id = fields.Many2one(
        comodel_name='opsol_costadoro.metrique_equip',
        string='Metric',
    )
    uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Unite de mesure',
        related="metric_id.uom_id"
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Client',
        related="equipment_id.client"
    )
    serial_no = fields.Char(related="equipment_id.serial_no")
    reference_intervention = fields.Float(
        string='Reference Intervention',
        help="""Valeur reference pour declencher une nouvelle intervention sur l'equipement."""
    )
    current_measure = fields.Float(
        string='valeur Actuelle',
        compute="compute_current_measure",
        store=True
    )
    progress_metric = fields.Float(
        string='Progress',
        compute="compute_progress_metric",
        store=True
    )
    progress_metric_per = fields.Char(
        string='Progress',
        compute="compute_progress_metric",
        store=True
    )
    p_create_intervention = fields.Char(
        string='Need intervention ?',
        compute="compute_progress_metric",
        store=True
    )
    entries_ids = fields.One2many(
        comodel_name='opsol_costadoro.metric_entry',
        inverse_name='line_metric_id',
        string='Entries',
    )
    use_hour = fields.Boolean(
        string='Use Hour',
        compute="compute_use_hour",
        store=True,
    )
    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection(
        string="Etat",
        selection=[('normal', 'Normal'),('inter', 'Need Intervention')],
        default="normal"
    )

    @api.depends("serial_no", "metric_id")
    def compute_name(self):
        for rec in self:
            rec.name = f"{rec.serial_no} - {rec.metric_id.name}"

    @api.depends("uom_id")
    def compute_use_hour(self):
        uom_hour = self.env.ref("uom.product_uom_hour")
        if not uom_hour:
            raise UserError(_("l'unite de mesure de base heure est manquante, veuillez svp corriger cette erreur."))
        for rec in self:
            rec.use_hour = rec.uom_id.id == uom_hour.id or False

    @api.depends('current_measure', 'progress_metric')
    def compute_progress_metric(self):
        for rec in self:
            ref_val = rec.reference_intervention
            rec.progress_metric = ref_val and rec.current_measure * 1.0 / ref_val or 0
            rec.progress_metric_per = f"{rec.progress_metric * 100:.1f} %"
            rec.p_create_intervention = True if rec.progress_metric >= 1.0 else False

    @api.depends("entries_ids.value")
    def compute_current_measure(self):
        for rec in self:
            rec.current_measure = sum(rec.entries_ids.mapped("value"))

    def action_addentry(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("opsol_costadoro.action_eq_addentry_wiz")
        action['context'] = {'default_equipment_id': self.equipment_id.id, 'default_line_metric_id': self.id}
        return action

    @api.model
    def update_time_metric(self):
        elts = self.env["opsol_costadoro.line_metric"].search([
            ('use_hour', '=', True), ('active', '=', True)])
        now_today = datetime.now()
        values = []
        for elt in elts:
            last_entry = elt.entries_ids and elt.entries_ids.filtered(lambda v: v.date_end).sorted(key=lambda r: r.date_end, reverse=True) or None
            date_last_entry = last_entry and last_entry[0].date_end or now_today
            equip=elt.equipment_id.name

            diff = now_today - date_last_entry

            val = {
                'line_metric_id': elt.id,
                'value': (diff.seconds / 3600.0 + diff.days * 24),
                'note': _("Utilisation equipement %(equip)s de '%(debut)s' a '%(fin)s'",equip=equip, debut=date_last_entry, fin=now_today),
                'date_start': date_last_entry, 'date_end': now_today,
            }
            values.append(val)

        for _val in values:
            self.env["opsol_costadoro.metric_entry"].create(_val)

    def reinit_values(self):
        values = []
        for rec in self:
            equip=rec.equipment_id.name
            now_today = datetime.now()
            val = {
                'line_metric_id': rec.id, 'value': -1 * rec.current_measure,
                'note': _("Reinitialisation indicateurs equipement %(equip)s",equip=equip),
                'date_start': now_today, 'date_end': now_today,
            }
            values.append(val)

        for _val in values:
            self.env["opsol_costadoro.metric_entry"].create(_val)

    def action_open_entries(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("opsol_costadoro.action_metric_entry")
        action['domain'] = [('id', 'in', self.entries_ids.ids)]
        return action

    def create_prev_intervention(self):
        for rec in self:
            rec.equipment_id.create_intervention(prevent=True)
            rec.state = 'inter'

    @api.constrains('current_measure', 'progress_metric')
    def force_update_state(self):
        for rec in self:
            rec.state = 'normal' if rec.progress_metric < 1.0 else 'inter'
