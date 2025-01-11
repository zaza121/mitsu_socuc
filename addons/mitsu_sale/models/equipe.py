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
    employee_ids = fields.Many2many(
        comodel_name='hr.employee',
        string='Employee',
        relation="equipe_to_emp"
    )
    resource_ids = fields.Many2many(
        comodel_name='resource.resource',
        string='Resources',
        compute="compute_resource_ids"
    )
    manager_id = fields.Many2one(
        comodel_name='res.users',
        string='Manager'
    )

    @api.depends("employee_ids")
    def compute_resource_ids(self):
        for rec in self:
            rec.resource_ids = rec.employee_ids.mapped("resource_id")
