from odoo import models, fields, api

class ProjectProject(models.Model):
    _inherit = 'project.project'
    
    project_type = fields.Selection([
        ('external', 'Externe (Facturable)'),
        ('internal', 'Interne (Dépenses uniquement)')
    ], string="Type de Projet", default='external', required=True)
    
    @api.model
    def create(self, vals):
        if vals.get('sale_line_id') or self.env.context.get('default_sale_order_id'):
            vals = dict(vals)
            vals['project_type'] = 'external'
        return super(ProjectProject, self).create(vals)