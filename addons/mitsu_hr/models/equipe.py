# -*- coding: utf-8 -*-
from odoo import api, fields, models


class MitsuHrEquipe(models.Model):
    _name = 'mitsu_hr.equipe'
    _description = "Equipe Mitsu HR"
    _rec_name = "name"

    name = fields.Char(string='Nom', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    departments_ids = fields.Many2many(
        comodel_name='hr.department',
        string='Départements',
        relation="equipe_to_depart"
    )
    extra_employee_ids = fields.Many2many(
        comodel_name='hr.employee',
        string='Autre(s) Employés',
        relation="equipe_to_extra_emp",
    )
    # employee_ids calculé : membres des départements + extra_employee_ids
    employee_ids = fields.Many2many(
        comodel_name='hr.employee',
        string='Employés',
        relation="equipe_to_emp",
        compute="_compute_employee_ids",
        readonly=False,
        store=True,
    )
    resource_ids = fields.Many2many(
        comodel_name='resource.resource',
        string='Resources',
        compute="_compute_employee_ids",
        store=True,
    )
    manager_id = fields.Many2one(
        comodel_name='res.users',
        string='Manager'
    )

    @api.depends('departments_ids.member_ids', 'extra_employee_ids')
    def _compute_employee_ids(self):
        for rec in self:
            employees = rec.departments_ids.mapped("member_ids")
            employees |= rec.extra_employee_ids
            rec.employee_ids = employees
            rec.resource_ids = employees.mapped("resource_id")
