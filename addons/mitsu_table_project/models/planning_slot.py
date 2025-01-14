from odoo import  fields, models, _, api


class ResPartnerContact(models.Model):
    _inherit = 'planning.slot'
    
   
    quantity_table = fields.Float(_("Quantité"), compute="_compute_quantity_table")
    price_unit_table = fields.Float(_("Prix Unitaire"), compute="_compute_price_unit_table")
    time_task_table = fields.Float(_("Temps sur la tâche"), compute="_compute_time_task_table")
    time_to_plan  = fields.Float(_("Temps à planifier"), compute="_compute_time_to_plan")
    time_to_realize = fields.Float(_("Temps réaliser"), compute="_compute_time_to_realize")
    time_to_realize_effective = fields.Float(_("Temps à réaliser"), 
        compute="_compute_time_to_realize_effective" )
    hourly_cost_table = fields.Float(_("Coût unitaire de l'employée"),compute="_compute_hourly_cost")
    employee_cost_total_task = fields.Float(_("Coût total de l'employée"),compute="_compute_employee_cost_total_task")
    projected_sales = fields.Float(_("CA prévisionnel"),compute="_compute_projected_sales")
    marged_sales = fields.Float(_("Marge prévisionnel"),compute="_compute_marged_sales")
    projected_sales_realize = fields.Float(_("CA réaliser"),compute="_compute_projected_sales_realize")
    employee_real_cost = fields.Float(_("Coût réel de l'employée"),compute="_compute_employee_real_cost")
    marged_realize = fields.Float(_("Marge réaliser"),compute="_compute_marged_realize")
    margin_difference = fields.Float(_("Différence de marge"),compute="_compute_margin_difference")

    @api.depends('sale_line_id')
    def _compute_quantity_table(self):
        for rec in self:
            rec.quantity_table = rec.sale_line_id.product_uom_qty

    @api.depends('sale_line_id')
    def _compute_price_unit_table(self):
        for rec in self:
            rec.price_unit_table = rec.sale_line_id.price_unit

    @api.depends('task_id')
    def _compute_time_task_table(self):
        for rec in self:
            rec.time_task_table = rec.task_id.allocated_hours

    @api.depends('task_id')
    def _compute_time_to_plan(self):
        for rec in self:
            rec.time_to_plan = rec.time_task_table - rec.allocated_hours

    @api.depends('task_id')
    def _compute_time_to_realize(self):
        for rec in self:
            rec.time_to_realize = rec.task_id.effective_hours

    @api.depends('task_id')
    def _compute_time_to_realize_effective(self):
        for rec in self:
            rec.time_to_realize_effective = rec.allocated_hours - rec.time_to_realize

    @api.depends('employee_id')
    def _compute_hourly_cost(self):
        for rec in self:
            rec.hourly_cost_table = rec.employee_id.hourly_cost

    @api.depends('employee_id')
    def _compute_employee_cost_total_task(self):
        for rec in self:
            rec.employee_cost_total_task = rec.time_task_table * rec.employee_id.hourly_cost

    @api.depends('employee_id')
    def _compute_projected_sales(self):
        for rec in self:
            rec.projected_sales = rec.price_unit_table * rec.time_task_table

    @api.depends('employee_id')
    def _compute_marged_sales(self):
        for rec in self:
            rec.marged_sales = rec.projected_sales - rec.employee_cost_total_task

    @api.depends('employee_id')
    def _compute_projected_sales_realize(self):
        for rec in self:
            rec.projected_sales_realize = rec.hourly_cost_table * rec.time_to_realize_effective

    @api.depends('employee_id')
    def _compute_employee_real_cost(self):
        for rec in self:
            rec.employee_real_cost = rec.hourly_cost_table * rec.time_to_realize

    @api.depends('employee_id')
    def _compute_marged_realize(self):
        for rec in self:
            rec.marged_realize = rec.projected_sales_realize - rec.employee_real_cost

    @api.depends('employee_id')
    def _compute_margin_difference(self):
        for rec in self:
            rec.margin_difference = rec.marged_realize - rec.marged_sales      
            

    


    
