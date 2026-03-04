from odoo import models, fields, api

class ProjectProject(models.Model):
    _inherit = 'project.project'

    employee_team_id = fields.Many2one(
        'hr.employee.team', 
        string='Équipe du responsable', 
        compute='_compute_employee_team_id', 
        store=True
    )

    @api.depends('user_id')
    def _compute_employee_team_id(self):
        for project in self:
            if project.user_id:
                employee = self.env['hr.employee'].search([('user_id', '=', project.user_id.id)], limit=1)
                # On récupère la première équipe de l'employé
                project.employee_team_id = employee.team_ids[:1].id if employee and employee.team_ids else False
            else:
                project.employee_team_id = False