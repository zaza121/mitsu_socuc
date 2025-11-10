# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools.float_utils import float_round


class PlanningSlot(models.Model):
    _inherit = 'planning.slot'

    quantity_table = fields.Float(_("Quantité"), compute="_compute_quantity_table", store=True)
    price_unit_table = fields.Float(_("Prix Unitaire"), compute="_compute_price_unit_table", store=True)
    time_task_table = fields.Float(_("Temps sur la tâche"), compute="_compute_time_task_table", store=True)
    time_to_plan = fields.Float(_("Temps à planifier"), compute="_compute_time_to_plan", store=True)
    time_to_realize = fields.Float(_("Temps réalisé"), compute="_compute_time_to_realize", store=True)
    time_to_realize_effective = fields.Float(_("Temps à réaliser"), compute="_compute_time_to_realize_effective", store=True)
    hourly_cost_table = fields.Float(_("Coût unitaire de l'employé"), compute="_compute_hourly_cost", store=True)
    employee_cost_total_task = fields.Float(_("Coût total de l'employé"), compute="_compute_employee_cost_total_task", store=True)
    projected_sales = fields.Float(_("CA prévisionnel"), compute="_compute_projected_sales", store=True)
    marged_sales = fields.Float(_("Marge prévisionnelle"), compute="_compute_marged_sales", store=True)
    projected_sales_realize = fields.Float(_("CA réalisé"), compute="_compute_projected_sales_realize", store=True)
    employee_real_cost = fields.Float(_("Coût réel de l'employé"), compute="_compute_employee_real_cost", store=True)
    marged_realize = fields.Float(_("Marge réalisée"), compute="_compute_marged_realize", store=True)
    margin_difference = fields.Float(_("Différence de marge"), compute="_compute_margin_difference", store=True)
    currency_id = fields.Many2one(related='sale_line_id.currency_id', store=True, readonly=True)
    date_start = fields.Date(string='Date', related='project_id.date_start', store=True)
    task_id = fields.Many2one(
        string="Tache",
        comodel_name='project.task'
    )

    @api.depends('sale_line_id.product_uom_qty')
    def _compute_quantity_table(self):
        for rec in self:
            rec.quantity_table = rec.sale_line_id.product_uom_qty if rec.sale_line_id else 0.0

    @api.depends('sale_line_id.price_unit')
    def _compute_price_unit_table(self):
        for rec in self:
            rec.price_unit_table = rec.sale_line_id.price_unit if rec.sale_line_id else 0.0

    @api.depends('task_id.allocated_hours')
    def _compute_time_task_table(self):
        for rec in self:
            rec.time_task_table = rec.task_id.allocated_hours if rec.task_id else 0.0

    @api.depends('time_task_table', 'allocated_hours')
    def _compute_time_to_plan(self):
        for rec in self:
            rec.time_to_plan = (rec.time_task_table or 0.0) - (rec.allocated_hours or 0.0)

    @api.depends('task_id.effective_hours')
    def _compute_time_to_realize(self):
        for rec in self:
            rec.time_to_realize = rec.task_id.effective_hours if rec.task_id else 0.0

    @api.depends('allocated_hours', 'time_to_realize')
    def _compute_time_to_realize_effective(self):
        for rec in self:
            rec.time_to_realize_effective = (rec.allocated_hours or 0.0) - (rec.time_to_realize or 0.0)

    @api.depends('employee_id.hourly_cost')
    def _compute_hourly_cost(self):
        for rec in self:
            rec.hourly_cost_table = rec.employee_id.hourly_cost or 0.0

    @api.depends('time_task_table', 'hourly_cost_table')
    def _compute_employee_cost_total_task(self):
        for rec in self:
            rec.employee_cost_total_task = (rec.time_task_table or 0.0) * (rec.hourly_cost_table or 0.0)

    @api.depends('price_unit_table', 'time_task_table')
    def _compute_projected_sales(self):
        for rec in self:
            rec.projected_sales = (rec.price_unit_table or 0.0) * (rec.time_task_table or 0.0)

    @api.depends('projected_sales', 'employee_cost_total_task')
    def _compute_marged_sales(self):
        for rec in self:
            rec.marged_sales = (rec.projected_sales or 0.0) - (rec.employee_cost_total_task or 0.0)

    @api.depends('sale_line_id.qty_invoiced', 'sale_line_id.price_unit')
    def _compute_projected_sales_realize(self):
        for rec in self:
            if rec.sale_line_id:
                rec.projected_sales_realize = (rec.sale_line_id.qty_invoiced or 0.0) * (rec.sale_line_id.price_unit or 0.0)
            else:
                rec.projected_sales_realize = 0.0

    @api.depends('hourly_cost_table', 'time_to_realize')
    def _compute_employee_real_cost(self):
        for rec in self:
            rec.employee_real_cost = (rec.hourly_cost_table or 0.0) * (rec.time_to_realize or 0.0)

    @api.depends('projected_sales_realize', 'employee_real_cost')
    def _compute_marged_realize(self):
        for rec in self:
            rec.marged_realize = (rec.projected_sales_realize or 0.0) - (rec.employee_real_cost or 0.0)

    @api.depends('marged_realize', 'marged_sales')
    def _compute_margin_difference(self):
        for rec in self:
            rec.margin_difference = (rec.marged_realize or 0.0) - (rec.marged_sales or 0.0)