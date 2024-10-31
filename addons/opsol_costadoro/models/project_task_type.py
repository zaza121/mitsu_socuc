# -*- coding: utf-8 -*-

from odoo import api, fields, models

class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'
    
    remove_analines = fields.Boolean(
        string='Remove Analytic Lines?',
        default=False,
        help="Remove account line when a task in move to this step"
    )
