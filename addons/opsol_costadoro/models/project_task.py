# -*- coding: utf-8 -*-

from odoo import api, fields, models

class ProjectTask(models.Model):
    _inherit = 'project.task'
    
    type_intervention = fields.Selection(
        selection=[
            ('install', 'Installation'),
            ('reprise', 'Reprise'),
            ('depann', 'Dépannage'),
            ('prevent', 'Préventif'),
            ('revisi', 'Révision'),
            ('detart', 'Détartrage'),
            ('format', 'Formation'),
            ('qualit', 'Qualité'),
        ],
        string="Type Intervention",
        default="depann",
    )
    facturer_intervention = fields.Boolean(
        string='Facturer Intervention',
        compute="compute_facturer_intervention",
        store=True,
        readonly=False,
    )
    localisation_intervention = fields.Selection(
        string="Localisation Intervention",
        required=True,
        selection=[('client', "Client"),('entre', "Entrepot")],
        default="client"
    )
    quick_equipment_ids = fields.Many2many(
        comodel_name='equipment.details',
        string='Equipements',
        compute="compute_quick_equipment_ids",
        store=True
    )
    lines_metric_ids = fields.Many2many(
        comodel_name='opsol_costadoro.line_metric',
        compute="compute_quick_equipment_ids",
        string='Lignes de metrique',
        store=True
    )
    types_equip_ids = fields.Many2many(
        comodel_name='equipment.category',
        compute="compute_quick_equipment_ids",
        string='Type equipements',
        store=True
    )
    model_equip_ids = fields.Many2many(
        comodel_name='opsol_costadoro.model_equip',
        compute="compute_quick_equipment_ids",
        string='Modeles',
        store=True
    )
    manufacturer_ids = fields.Many2many(
        comodel_name='equipment.manufacturer',
        compute="compute_quick_equipment_ids",
        string='Fabricants',
        store=True
    )
    force_ana_acc_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic Account',
    )

    @api.depends('project_id.analytic_account_id', "force_ana_acc_id")
    def _compute_analytic_account_id(self):
        force_analytic_acc = self.filtered(lambda x: x.force_ana_acc_id)
        for rec in force_analytic_acc:
            rec.analytic_account_id = rec.force_ana_acc_id

        no_equipment = self - force_analytic_acc
        return super(ProjectTask, no_equipment)._compute_analytic_account_id()

    @api.depends("equipment_ids.equipment")
    def compute_quick_equipment_ids(self):
        for rec in self:
            rec.quick_equipment_ids = rec.equipment_ids.mapped(lambda x: x.equipment)
            rec.lines_metric_ids = rec.quick_equipment_ids.mapped("lines_metric_ids")
            rec.types_equip_ids = rec.quick_equipment_ids.mapped("category_id")
            rec.model_equip_ids = rec.quick_equipment_ids.mapped("equip_model_id")
            rec.manufacturer_ids = rec.quick_equipment_ids.mapped("manufacturer_id")

    @api.depends("partner_id")
    def compute_facturer_intervention(self):
        for rec in self:
            if rec.partner_id:
                rec.facturer_intervention = rec.partner_id.facturer_intervention
            else:
                rec.facturer_intervention = True

    def reinit_metric_equipment(self):
        prevent_intervention = self.filtered(lambda x: x.type_intervention == 'prevent')
        client_equips = prevent_intervention.mapped('equipment_ids.equipment')
        client_equips.reset_indicators()

    @api.constrains("stage_id")
    def delete_accounting_analytic(self):
        for rec in self:
            if rec.stage_id and rec.stage_id.remove_analines:
                # remove all timesheet
                rec.timesheet_ids.unlink()
