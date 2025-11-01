# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError


class ReportPla(models.Model):
    _name = 'mitsu_table_project.reportpla'
    _description = "Rapport planning"
    _auto = False
    # Reste de l'héritage pour les mixins non critiques retiré pour la concision de l'exemple
    
    create_date = fields.Datetime("Creation Date")
    start_datetime = fields.Datetime()
    end_datetime = fields.Datetime()
    sale_line_id = fields.Many2one('sale.order.line', string='Sales Order Item')
    sale_order_id = fields.Many2one('sale.order', string='Sales Order', related='sale_line_id.order_id', store=True)
    employee_id = fields.Many2one('hr.employee', 'Employee')
    allocated_hours = fields.Float(string='Allocated Hours', compute_sudo=True)
    project_id = fields.Many2one('project.project')
    task_id = fields.Many2one("project.task", string="Task")
    company_id = fields.Many2one(comodel_name="res.company", string="Societe")
    department_id = fields.Many2one(comodel_name="hr.department", string="Departement")
    manager_id = fields.Many2one(comodel_name='hr.employee')
    name = fields.Char(string='Name')
    state = fields.Selection([('draft', 'Draft'), ('published', 'Published')], string='Status', default='draft')
    resource_type = fields.Selection([("user", "Human"), ("material", "Material")], string="Type", default="user", readonly=True)
    quantity_table = fields.Float(_("Quantité"))
    price_unit_table = fields.Float("Prix Unitaire")
    time_task_table = fields.Float(_("Temps sur la tâche"))
    time_to_plan = fields.Float("Temps à planifier", compute="_compute_time_to_plan")
    time_to_realize = fields.Float("Temps réalisé")
    hourly_cost_table = fields.Float("Coût unitaire de l'employé")
    projected_sales = fields.Float(_("CA prévisionnel"), compute="_compute_projected_sales")
    marged_sales = fields.Float(_("Marge prévisionnelle"), compute="_compute_marged_sales")
    projected_sales_realize = fields.Float(_("CA réalisé"), compute="_compute_projected_sales_realize")
    employee_real_cost = fields.Float("Coût réel de l'employé", compute="_compute_employee_real_cost")
    marged_realize = fields.Float(_("Marge réalisée"), compute="_compute_marged_realize")
    margin_difference = fields.Float(_("Différence de marge"), compute="_compute_margin_difference")
    currency_id = fields.Many2one(related='sale_line_id.currency_id')
    date_start = fields.Date(string='Date', related='project_id.date_start')
    boni_mali = fields.Selection([("bon", "BONI"), ("mal", "MALI")], string="BONI/MALI", compute="_compute_boni_mali", store=True)

    @api.depends('time_task_table', 'allocated_hours')
    def _compute_time_to_plan(self):
        for rec in self:
            rec.time_to_plan = (rec.time_task_table or 0.0) - (rec.allocated_hours or 0.0)

    @api.depends('price_unit_table', 'time_task_table')
    def _compute_projected_sales(self):
        for rec in self:
            rec.projected_sales = (rec.price_unit_table or 0.0) * (rec.time_task_table or 0.0)

    @api.depends('projected_sales', 'hourly_cost_table', 'time_task_table')
    def _compute_marged_sales(self):
        for rec in self:
            cost_total = (rec.hourly_cost_table or 0.0) * (rec.time_task_table or 0.0)
            rec.marged_sales = (rec.projected_sales or 0.0) - cost_total

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

    @api.depends('projected_sales_realize', 'employee_real_cost')
    def _compute_boni_mali(self):
        for rec in self:
            rec.boni_mali = 'bon' if (rec.projected_sales_realize or 0.0) >= (rec.employee_real_cost or 0.0) else 'mal'

    def _select(self):
        return """
            SELECT
                MIN(ps.id) AS id,
                MIN(ps.company_id) AS company_id,
                MIN(ps.department_id) AS department_id,
                MIN(ps.manager_id) AS manager_id,
                MIN(ps.name) AS name,
                MIN(ps.state) AS state,
                MIN(R.resource_type) AS resource_type,
                MIN(ps.role_id) AS role_id,
                ps.resource_id,
                ps.sale_line_id,
                ps.task_id,
                ps.employee_id,
                ps.template_id,
                ps.project_id,
                MIN(ps.start_datetime) AS start_datetime,
                MIN(ps.end_datetime) AS end_datetime,
                SUM(ps.allocated_hours) AS allocated_hours,
                MIN(ps.create_date) AS create_date,
                MIN(sol.price_unit) AS price_unit_table,
                MIN(sol.product_uom_qty) AS quantity_table,
                MIN(tsk.allocated_hours) AS time_task_table,
                MIN(tsk.effective_hours) AS time_to_realize,
                MIN(emp.hourly_cost) AS hourly_cost_table
        """

    def _from(self):
        return """
            FROM planning_slot AS ps
        """

    def _join(self):
        return """
            LEFT JOIN sale_order_line sol ON ps.sale_line_id = sol.id
            LEFT JOIN project_task tsk ON ps.task_id = tsk.id
            LEFT JOIN hr_employee emp ON ps.employee_id = emp.id
            LEFT JOIN resource_resource R ON R.id = ps.resource_id
        """

    def _where(self):
        return """"""

    def _group_by(self):
        return """
            GROUP BY ps.sale_line_id, ps.project_id, ps.task_id, ps.resource_id,
ps.employee_id, ps.template_id
        """

    def init(self):
        tools.drop_view_if_exists(self._cr, self._table)
        self._cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                %s
                %s
                %s
                %s
                %s
            )
        """ % (self._table, self._select(), self._from(),
self._join(), self._where(), self._group_by())
        )