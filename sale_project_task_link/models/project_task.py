from odoo import fields, models

class ProjectTask(models.Model):
    _inherit = "project.task"

    template_task_id = fields.Many2one(
        "project.task",
        string="Tâche modèle d'origine",
        readonly=True,
        help="Référence vers la tâche du template copiée."
    )

    sale_line_id = fields.Many2one(
        "sale.order.line",
        string="Ligne de commande",
        help="Ligne de commande à l’origine de cette tâche."
    )

    product_id = fields.Many2one(
        "product.product",
        string="Produit",
        help="Produit lié à cette tâche."
    )
