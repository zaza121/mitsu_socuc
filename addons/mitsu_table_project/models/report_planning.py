from odoo import  fields, models, tools, _, api


class ReportPla(models.Model):
    _auto = False
    _name = 'mitsu_table_project.reportpla'
    _inherit = ['resource.mixin']
    _description = "Rapport planning"

    create_date = fields.Datetime("Creation Date")
    start_datetime = fields.Datetime(required=False)
    end_datetime = fields.Datetime(required=False)
    sale_line_id = fields.Many2one('sale.order.line', string='Sales Order Item',
        help="Sales order item for which this shift will be performed. When sales orders are automatically planned,"
             " the remaining hours of the sales order item, as well as the role defined on the service, are taken into account."
    )
    sale_order_id = fields.Many2one('sale.order', string='Sales Order', related='sale_line_id.order_id', store=True)
    role_product_ids = fields.One2many('product.template', related='role_id.product_ids')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    sale_line_plannable = fields.Boolean(related='sale_line_id.product_id.planning_enabled')
    allocated_hours = fields.Float(compute_sudo=True)
    role_id = fields.Many2one(
        'planning.role', string="Role",
        help="Define the roles your resources perform (e.g. Chef, Bartender, Waiter...). Create open shifts for the roles you need to complete a mission. Then, assign those open shifts to the resources that are available."
    )
    template_id = fields.Many2one('planning.slot.template', string='Shift Templates', compute='_compute_template_id', readonly=False, store=True)
    project_id = fields.Many2one('project.project')
    task_id = fields.Many2one("project.task", string="Task")
    company_id = fields.Many2one(comodel_name="res.company", string="Societe")    
    department_id = fields.Many2one(comodel_name="hr.department", string="Departement")
    manager_id = fields.Many2one(comodel_name='hr.employee')
    name = fields.Char(string='Name')
    state = fields.Selection([
            ('draft', 'Draft'),
            ('published', 'Published'),
    ], string='Status', default='draft')
    resource_type = fields.Selection([
        ("user", "Human"),
        ("material", "Material")], string="Type",
        default="user", readonly=True)

    quantity_table = fields.Float(_("Quantité"))
    price_unit_table = fields.Float("Prix Unitaire")
    time_task_table = fields.Float(_("Temps sur la tâche"))
    time_to_plan  = fields.Float("Temps à planifier", compute="_compute_time_to_plan")
    time_to_realize = fields.Float("Temps réalisé")
    time_to_realize_effective = fields.Float("Temps à réaliser", compute="_compute_time_to_realize_effective")
    hourly_cost_table = fields.Float("Coût unitaire de l'employé")
    employee_cost_total_task = fields.Float(_("Coût total de l'employé"),compute="_compute_employee_cost_total_task")
    projected_sales = fields.Float(_("CA prévisionnel"),compute="_compute_employee_cost_total_task")
    marged_sales = fields.Float(_("Marge prévisionnelle"),compute="_compute_employee_cost_total_task")
    projected_sales_realize = fields.Float(_("CA réalisé"),compute="_compute_projected_sales_realize")
    employee_real_cost = fields.Float("Coût réel de l'employé", compute="_compute_employee_cost_total_task")
    marged_realize = fields.Float(_("Marge réalisée"),compute="_compute_employee_cost_total_task")
    margin_difference = fields.Float(_("Différence de marge"),compute="_compute_employee_cost_total_task")
    currency_id = fields.Many2one(related='sale_line_id.currency_id')
    date_start = fields.Date(string='Date', related='project_id.date_start')
    manager_ids = fields.Many2many(
        comodel_name='res.users',
        string='Resources',
        compute="_compute_employee_cost_total_task",
        search = '_search_manager_ids'
    )
    boni_mali = fields.Selection([("bon", "BONI"),("mal", "MALI")], string="BONI/MALI", compute="_compute_employee_cost_total_task")

    def _search_manager_ids(self, operator, value):
        user = self.env.user
        equipe_manager = self.env["mitsu_hr.equipe"].search([('manager_id', '=', user.id)])
        members = equipe_manager.mapped('employee_ids')
        return [('employee_id', 'in', members.ids)]

    @api.depends('task_id')
    def _compute_time_to_realize_effective(self):
        for rec in self:
            rec.time_to_realize_effective = rec.allocated_hours - rec.time_to_realize

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
                MIN(ps.allocated_hours) AS allocated_hours,
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
            LEFT JOIN resource_resource R ON R.id = pS.resource_id
        """

    def _where(self):
        disccusion_subtype = self.env.ref('mail.mt_comment')
        return """"""
        # return """
        #     WHERE
        #         m.model = 'crm.lead' AND (m.mail_activity_type_id IS NOT NULL OR m.subtype_id = %s)
        # """ % (disccusion_subtype.id,)

    def _group_by(self):
        return """
            GROUP BY ps.sale_line_id, ps.project_id, ps.task_id, ps.resource_id, ps.employee_id, ps.template_id

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
        """ % (self._table, self._select(), self._from(), self._join(), self._where(), self._group_by())
        )

    def _compute_time_to_plan(self):
        for rec in self:
            rec.time_to_plan = rec.time_task_table - rec.allocated_hours
    
    @api.depends('employee_id', 'template_id')
    def _compute_role_id(self):
        for slot in self:
            if not slot.role_id:
                if slot.employee_id.default_planning_role_id:
                    slot.role_id = slot.employee_id.default_planning_role_id
                else:
                    slot.role_id = False

            if slot.template_id:
                slot.previous_template_id = slot.template_id
                if slot.template_id.role_id:
                    slot.role_id = slot.template_id.role_id
            elif slot.previous_template_id and not slot.template_id and slot.previous_template_id.role_id == slot.role_id:
                slot.role_id = False

    @api.depends('employee_id')
    def _compute_employee_cost_total_task(self):
        for rec in self:
            rec.employee_cost_total_task = rec.time_task_table * rec.hourly_cost_table
            rec.projected_sales = rec.price_unit_table * rec.time_task_table
            rec.marged_sales = rec.projected_sales - rec.employee_cost_total_task
            rec.employee_real_cost = rec.hourly_cost_table * rec.time_to_realize
            rec.marged_realize = rec.employee_real_cost - rec.projected_sales_realize
            rec.margin_difference = rec.projected_sales_realize - rec.employee_real_cost - rec.marged_sales
            # rec.manager_ids = rec.mapped("employee_id.equipe_ids.manager_id")
            rec.manager_ids = False
            rec.boni_mali = "bon" if rec.marged_realize > 0 else "mal"

    @api.depends('sale_line_id')
    def _compute_projected_sales_realize(self):
        for rec in self:
            rec.projected_sales_realize = rec.sale_line_id.qty_invoiced * rec.sale_line_id.price_unit
