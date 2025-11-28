# -*- coding: utf-8 -*-
from odoo import api, fields, models, Command, _
from odoo.osv import expression
from odoo.exceptions import ValidationError
from datetime import datetime


class ProjectProject(models.Model):
    _inherit = 'project.project'

    temp_task_ids = fields.One2many(
        comodel_name='mitsu_sale.project_temp_task',
        inverse_name='project_temp_id',
        string='Template taches',
    )

    @api.constrains('label_tasks')
    def create_task_ids(self):
        pttask_obj = self.env["mitsu_sale.project_temp_task"]
        for rec in self:
            labels = rec.label_tasks.split(",")
            to_delete = rec.temp_task_ids.filtered(lambda x: x.name not in labels)
            if to_delete:
                to_delete.unlink()
            to_create = [x for x in labels if x not in rec.mapped('temp_task_ids.name')]
            for elt in to_create:
                result = pttask_obj.create({'name': elt, 'project_temp_id': rec.id})
