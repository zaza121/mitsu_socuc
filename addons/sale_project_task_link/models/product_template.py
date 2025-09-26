from odoo import fields, models

class ProductTemplate(models.Model):
    _inherit = "product.template"

    task_template_id = fields.Many2one(
        "project.task",
        string="Tâche du template",
        help="Associer ce produit à une tâche d’un projet modèle."
    )
