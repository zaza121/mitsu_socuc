# -*- coding: utf-8 -*-
from odoo import api, fields, models


class hrEquipe(models.Model):
    _name= 'mitsu_hr.equipe'
    _rec_name = "name"

    name = fields.Char(string='Nom')
    sequence = fields.Integer(string='Sequence')
    departments_ids = fields.Many2many(
        comodel_name='hr.department',
        string='Departements',
        relation="equipe_to_depart"
    )
    extra_employee_ids = fields.Many2many(
        comodel_name='hr.employee',
        string='Extra Employes',
        relation="equipe_to_extra_emp",
    )
    employee_ids = fields.Many2many(
        comodel_name='hr.employee',
        string='Employes',
        relation="equipe_to_emp",
        compute="compute_employee_ids",
        readonly=False,
        store=True,
    )
    employee_ids = fields.Many2many(
        comodel_name='hr.employee',
        string='Employee',
        relation="equipe_to_emp",
        compute="compute_employee_ids",
        readonly=False,
        store=True,
    )
    resource_ids = fields.Many2many(
        comodel_name='resource.resource',
        string='Resources',
        compute="compute_employee_ids"
    )
    manager_id = fields.Many2one(
        comodel_name='res.users',
        string='Manager'
    )

    @api.depends('departments_ids.member_ids', 'extra_employee_ids')
    def compute_employee_ids(self):
        for rec in self:
            employees = rec.departments_ids.mapped("member_ids")
            employees |= rec.extra_employee_ids
            rec.employee_ids = employees
            rec.resource_ids = employees.mapped("resource_id")
