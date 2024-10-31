
from odoo import api, models, fields

class AssessmentResponses(models.Model):
    _name = "jsa_pre.responses"
    _description = "Responses"

    name = fields.Char('Reference')
    task_id = fields.Integer(string='Task')
    active = fields.Boolean(default=True)
    question = fields.Char('Question')
    answer = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('na', 'N/A'), ], string='Answer', default='na')
