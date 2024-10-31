# -*- coding: utf-8 -*-
from odoo import models, fields, api, Command, _
from odoo.exceptions import UserError
from datetime import date
from odoo.osv import expression

COSTADORO_STATE = [('client', 'Chez le client'),('entre', "Entrepot"),('rebut', "Rebut")]


class EquipmentDetails(models.Model):
    _inherit = 'equipment.details'
    _rec_name = "serial_no"

    lines_metric_ids = fields.One2many(
        comodel_name='opsol_costadoro.line_metric',
        inverse_name='equipment_id',
        string='Lignes de metrique',
    )
    fsm_ids = fields.One2many(
        comodel_name='project.task',
        compute="compute_fsm_ids",
        string='Interventions',
        # store=True
    )
    sale_order_ids = fields.One2many(
        comodel_name='sale.order',
        compute="compute_fsm_ids",
        string='Bon de commande',
        # store=True
    )
    fsm_count = fields.Integer(
        string='Number of Intervention',
        compute="compute_fsm_ids",
        store=True
    )
    fsm_rev_count = fields.Integer(
        string='Number of Revisions',
        compute="compute_fsm_ids",
        store=True
    )
    fsm_count_prev = fields.Integer(
        string='Number of Intervention Preventive',
        compute="compute_fsm_ids",
        store=True
    )
    saleorder_count = fields.Integer(
        string='Number of Sale order',
        compute="compute_fsm_ids",
        store=True
    )
    last_intervention = fields.Date(
        string='Last Intervention',
        compute="compute_last_intervention",
        store=True
    )
    partner_history_ids = fields.One2many(
        comodel_name='opsol_costadoro.equip_move_history',
        inverse_name='equip_id',
        string='Historique',
    )
    move_ids = fields.Many2many(
        comodel_name='stock.move',
        relation="move_to_equip",
        string='Moves',
    )
    picking_number = fields.Integer(
        string='Number of picking',
        compute="compute_picking_number",
    )
    cost_state = fields.Selection(
        string="State",
        selection=COSTADORO_STATE,
        default="client",
        readonly=False
    )
    equip_model_id = fields.Many2one(
        comodel_name='opsol_costadoro.model_equip',
        string='Modele equipement',
    )
    date_debut = fields.Date(string='Date de mise a disposition')
    date_fin = fields.Date(string='Date fin nise a disposition')
    history_location_ids = fields.One2many(
        comodel_name='opsol_costadoro.equip_mvhistory_line',
        inverse_name='equip_id',
        string='History Location',
    )
    ana_acc_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic Account',
        compute="get_client_info",
        store=True,
        readonly=False,
    )
    name = fields.Char(
        string='Equipment Name', required=False, translate=False,
        compute="compute_name",
        store=True
    )

    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        domain = domain or []
        if name:
            domain = expression.OR([domain,[('serial_no', 'ilike', "%" + name + "%")]])
        return super()._name_search(name, domain, operator, limit, order)

    @api.depends("serial_no")
    def compute_name(self):
        for rec in self:
            rec.name = rec.serial_no

    @api.onchange('client')
    def _onchange_client(self):
        if self.client:
            self.street = self.client.street
            self.street2 = self.client.street2
            self.zip = self.client.zip
            self.city = self.client.city
            self.state = self.client.state_id
            self.country = self.client.country_id

    def save_change(self, obj, new_value):
        obj.create({
            'old_value': self.location,
            'new_value': new_value, 'equip_id': self.id
        })

    def write(self, vals):
        if 'location' in vals:
            mv_hist_obj = self.env["opsol_costadoro.equip_move_history"]
            for equip in self:
                equip.save_change(mv_hist_obj ,vals["location"])
        return super().write(vals)

    def compute_picking_number(self):
        for rec in self:
            rec.picking_number = len(rec.move_ids.mapped("picking_id"))

    @api.depends("jobs.service_date")
    def compute_last_intervention(self):
        for rec in self:
            jobs = rec.mapped("jobs.task_id").filtered(lambda x: x.type_intervention == "prevent").mapped("equipment_ids")
            jobs = jobs.filtered(lambda x: x.equipment.id == rec.id)
            rec.last_intervention = jobs and max(jobs.mapped("service_date")) or None

    @api.depends("client")
    def get_client_info(self):
        for rec in self:
            rec.ana_acc_id = rec.client and rec.client.ana_acc_id or None

    @api.depends("jobs.equipment", "jobs.task_id.stage_id")
    def compute_fsm_ids(self):
        pt_obj = self.env['project.task']
        for rec in self:
            task_ids = rec.mapped("jobs.task_id")
            rec.fsm_ids = task_ids
            fsm_ongoing = task_ids.filtered(lambda x: x.stage_id and x.stage_id.name not in ["Done", "Cancelled", "Termine", "Annule"])
            rec.sale_order_ids = task_ids.mapped("sale_order_id")
            rec.fsm_count = len(fsm_ongoing.filtered(lambda x: x.localisation_intervention == 'client' and x.type_intervention != 'prevent'))
            rec.fsm_rev_count = len(fsm_ongoing.filtered(lambda x: x.localisation_intervention == 'entre' and x.type_intervention != 'prevent'))
            rec.fsm_count_prev = len(fsm_ongoing.filtered(lambda x: x.type_intervention == 'prevent'))
            rec.saleorder_count = len(rec.sale_order_ids)

    def action_open_intervention(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("industry_fsm.project_task_action_fsm")
        action['domain'] = [('id', 'in', self.fsm_ids.filtered(lambda x: x.localisation_intervention == 'client' and x.type_intervention != 'prevent').ids)]
        action['context'] = {
            'fsm_mode': True, 'default_scale': 'day', 'default_localisation_intervention': 'client'}
        return action

    def action_open_revision(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("industry_fsm.project_task_action_fsm")
        action['domain'] = [('id', 'in', self.fsm_ids.filtered(lambda x: x.localisation_intervention == 'entre' and x.type_intervention != 'prevent').ids)]
        action['context'] = {
            'fsm_mode': True, 'default_scale': 'day', 'default_localisation_intervention': 'entre'}
        return action

    def action_open_intervention_prev(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("industry_fsm.project_task_action_fsm")
        action['domain'] = [('id', 'in', self.fsm_ids.filtered(lambda x: x.type_intervention == 'prevent').ids)]
        action['context'] = {
            'fsm_mode': True, 'default_scale': 'day', 'default_type_intervention': 'prevent' }
        return action

    def action_open_saleorder(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_quotations_with_onboarding")
        action['domain'] = [('id', 'in', self.sale_order_ids.ids)]
        return action

    def action_open_historique(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("opsol_costadoro.action_equip_move_history")
        action['domain'] = [('id', 'in', self.partner_history_ids.ids)]
        return action

    def action_open_picking(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_picking_tree_outgoing")
        action['domain'] = [('id', 'in', self.move_ids.mapped('picking_id.id'))]
        return action

    def create_intervention(self, prevent=False):
        self.ensure_one()
        if self.cost_state == "rebut":
            raise UserError(_("L'equipement est actuellement en rebut"))

        today = date.today()
        project = self.env.ref("industry_fsm.fsm_project")
        if not project:
            raise UserError(_("Projet for On Field Service not found"))

        values = {
            'name': f" Intervention - {today.strftime('%d %m %Y')}",
            'is_fsm': True,
            'user_ids': [self.env.user.id],
            'partner_id': self.client and self.client.id or None,
            'equipment_ids': [Command.create({'equipment': self.id})],
            'localisation_intervention': "client" if self.cost_state == "client" else "entre",
            'force_ana_acc_id': self.ana_acc_id and self.ana_acc_id.id or None
        }
        if prevent:
            values['type_intervention'] = "prevent"
        elt = self.env["project.task"].create(values)
        elt.project_id = project

        view_id = self.env.ref('project.view_task_form2', raise_if_not_found=False)
        action = self.env["ir.actions.actions"]._for_xml_id("industry_fsm.project_task_action_fsm")

        return {
            'name': elt.name, 'type': 'ir.actions.act_window',
            'target': 'current', 'res_model': 'project.task',
            'view_mode': 'form', 'view_id': view_id.id, 'res_id': elt.id,
        }

    def action_addentry(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("opsol_costadoro.action_eq_addentry_wiz")
        action['context'] = {'default_equipment_id': self.id}
        return action

    def reset_indicators(self):
        for rec in self:
            rec.lines_metric_ids.reinit_values()

    @api.constrains("client", "date_debut", "date_fin", "cost_state")
    def create_history_location(self):
        for rec in self:
            self.env["opsol_costadoro.equip_mvhistory_line"].create({
                'equip_id': rec.id, 'date': fields.Date.today(),
                'partner_id': rec.client and rec.client.id or False,
                'date_debut': rec.date_debut, 'date_fin': rec.date_fin,
                'cost_state': rec.cost_state
            })
