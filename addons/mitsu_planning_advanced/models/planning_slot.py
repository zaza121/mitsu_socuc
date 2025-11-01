from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Datetime

class PlanningSlot(models.Model):
    _inherit = 'planning.slot'

    user_id = fields.Many2one('res.users', compute='_compute_user_id', store=True)
    related_projects_ids = fields.Many2many('project.project', compute='_compute_related_projects')
    sol_ids = fields.Many2many('sale.order.line', compute='_compute_sol_ids')
    project_id = fields.Many2one('project.project')
    task_id = fields.Many2one('project.task')
    timesheet_id = fields.Many2one('account.analytic.line', string='Timesheet Entry')

    @api.depends('employee_id')
    def _compute_user_id(self):
        for rec in self:
            rec.user_id = rec.employee_id.user_id if rec.employee_id else False

    @api.depends('employee_id.user_id')
    def _compute_related_projects(self):
        for rec in self:
            if rec.employee_id.user_id:
                rec.related_projects_ids = self.env['project.task'].search([('user_ids','in',[rec.employee_id.user_id.id])]).mapped('project_id')
            else:
                rec.related_projects_ids = [(5,0,0)]

    @api.depends('employee_id.user_id','project_id')
    def _compute_sol_ids(self):
        for rec in self:
            if rec.project_id and rec.employee_id.user_id:
                rec.sol_ids = self.env['project.task'].search([
                    ('project_id','=',rec.project_id.id),
                    ('user_ids','in',[rec.employee_id.user_id.id])
                ]).mapped('sale_line_id')
            else:
                rec.sol_ids = [(5,0,0)]

    def generate_timesheet(self):
        for rec in self:
            if not rec.project_id or not rec.task_id:
                raise UserError(_("Please select both project and task."))
            if rec.timesheet_id:
                raise UserError(_("Timesheet already exists."))
            values = {
                'date': rec.start_datetime,
                'employee_id': rec.employee_id.id,
                'project_id': rec.project_id.id,
                'task_id': rec.task_id.id,
                'unit_amount': rec.allocated_hours,
            }
            rec.timesheet_id = self.env['account.analytic.line'].create(values)