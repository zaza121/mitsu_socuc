from odoo import models, fields, api

class ProjectTask(models.Model):
    _inherit = 'project.task'

    employee_team_id = fields.Many2one(
        'hr.employee.team', 
        string='Équipe assignée', 
        compute='_compute_employee_team_id', 
        store=True
    )

    @api.depends('user_ids') # Dans Odoo récent, les tâches peuvent avoir plusieurs utilisateurs
    def _compute_employee_team_id(self):
        for task in self:
            # On prend le premier utilisateur assigné pour déterminer l'équipe
            user = task.user_ids[:1]
            if user:
                employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
                task.employee_team_id = employee.team_ids[:1].id if employee and employee.team_ids else False
            else:
                task.employee_team_id = False