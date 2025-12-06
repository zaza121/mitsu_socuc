
from odoo import models, fields, api

class HrEmployeeTeam(models.Model):
    _name = 'hr.employee.team'
    _description = 'Équipe de Travail'
    _order = 'name'

    name = fields.Char(string="Nom de l'équipe", required=True)
    team_leader_id = fields.Many2one('hr.employee', string="Responsable d'équipe", required=True, ondelete='restrict')
    member_ids = fields.Many2many('hr.employee', 'hr_employee_team_member_rel', 'team_id', 'employee_id', string="Membres")
    member_count = fields.Integer(string='Nombre de membres', compute='_compute_member_count', store=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    @api.depends('member_ids')
    def _compute_member_count(self):
        for team in self:
            team.member_count = len(team.member_ids)

    @api.constrains('team_leader_id', 'member_ids')
    def _check_team_leader_in_members(self):
        for team in self:
            if team.team_leader_id and team.team_leader_id not in team.member_ids:
                team.member_ids = [(4, team.team_leader_id.id)]

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    team_ids = fields.Many2many('hr.employee.team', 'hr_employee_team_member_rel', 'employee_id', 'team_id', string="Équipes")
    managed_team_ids = fields.One2many('hr.employee.team', 'team_leader_id', string="Équipes gérées")
    is_team_leader = fields.Boolean(compute='_compute_is_team_leader', store=True)

    @api.depends('managed_team_ids')
    def _compute_is_team_leader(self):
        for emp in self:
            emp.is_team_leader = bool(emp.managed_team_ids)
