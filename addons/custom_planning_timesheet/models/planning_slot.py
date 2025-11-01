from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PlanningSlot(models.Model):
    _inherit = 'planning.slot'
    
    project_id = fields.Many2one('project.project', string="Projet")
    task_id = fields.Many2one('project.task', string="Tâche")
    role_id = fields.Many2one('hr.job', string="Rôle")
    # sale_line_name = fields.Char(related='sale_line_id.name', string="Article de BC", store=False)  # ← SUPPRIMÉ
    
    @api.onchange('resource_id')
    def _onchange_resource_filter_role(self):
        if self.resource_id and self.resource_id.user_id and self.resource_id.user_id.employee_id:
            employee = self.resource_id.user_id.employee_id
            if hasattr(employee, 'role_ids') and employee.role_ids:
                return {'domain': {'role_id': [('id', 'in', employee.role_ids.ids)]}}
        return {'domain': {'role_id': []}}
    
    @api.onchange('resource_id')
    def _onchange_resource_filter_project(self):
        if self.resource_id:
            planned_tasks = self.env['project.task'].search([
                ('planning_slot_ids.resource_id', '=', self.resource_id.id)
            ])
            project_ids = planned_tasks.mapped('project_id').ids
            return {'domain': {'project_id': [('id', 'in', project_ids)]}}
        return {'domain': {'project_id': []}}
    
    @api.onchange('project_id', 'resource_id')
    def _onchange_project_filter_task(self):
        domain = []
        if self.project_id:
            domain = [('project_id', '=', self.project_id.id)]
        if self.resource_id:
            planned_tasks = self.env['project.task'].search([
                ('planning_slot_ids.resource_id', '=', self.resource_id.id),
                ('project_id', '=', self.project_id.id)
            ])
            domain = [('id', 'in', planned_tasks.ids)]
        return {'domain': {'task_id': domain}}
    
    def action_generate_timesheet(self):
        self.ensure_one()
        if not self.project_id or not self.task_id or not self.resource_id:
            raise UserError(_("Veuillez renseigner la Ressource, le Projet et la Tâche pour générer une ligne de feuille de temps."))
        
        employee = False
        if self.resource_id.user_id and self.resource_id.user_id.employee_id:
            employee = self.resource_id.user_id.employee_id
        
        if not employee:
            raise UserError(_("La ressource sélectionnée n'est pas liée à un employé."))
        
        date = False
        if getattr(self, 'start_datetime', False):
            try:
                date = fields.Datetime.to_date(self.start_datetime)
            except Exception:
                date = fields.Date.context_today(self)
        
        vals = {
            'name': f"Planification {self.name or ''}",
            'date': date,
            'employee_id': employee.id,
            'project_id': self.project_id.id,
            'task_id': self.task_id.id,
            'unit_amount': self.duration or 0.0,
        }
        
        analytic_line = self.env['account.analytic.line'].create(vals)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Succès!'),
                'message': _('La ligne de feuille de temps a été générée.'),
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }