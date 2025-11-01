from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class ProjectTempTask(models.Model):
    _name = 'mitsu_sale.project_temp_task'
    _description = "Modèle de tâche de projet"
    _order = "name"

    name = fields.Char(
        string='Nom',
        required=True,
        help='Nom de la tâche modèle'
    )
    description = fields.Text(
        string='Description',
        help='Description détaillée de la tâche'
    )
    project_temp_id = fields.Many2one(
        'project.project',
        string='Projet modèle',
        ondelete='cascade',
        index=True
    )
    project_id = fields.Many2one(
        'project.project',
        string='Projet lié',
        ondelete='set null',
        help='Projet réel créé à partir de ce modèle'
    )
    product_temp_ids = fields.Many2many(
        'product.template',
        'product_2_projectpt_rel',
        'template_id', 'product_id',
        string='Produits associés',
        help='Produits qui déclenchent la création de cette tâche'
    )

    # Champs additionnels pour enrichir le modèle
    sequence = fields.Integer(
        string='Séquence',
        default=10,
        help='Ordre d\'affichage et de création des tâches'
    )
    planned_hours = fields.Float(
        string='Heures prévues',
        help='Nombre d\'heures estimées pour cette tâche'
    )
    user_ids = fields.Many2many(
        'res.users',
        string='Utilisateurs assignés',
        help='Utilisateurs qui seront automatiquement assignés à la tâche'
    )
    tag_ids = fields.Many2many(
        'project.tags',
        string='Étiquettes',
        help='Étiquettes à appliquer aux tâches créées'
    )

    _sql_constraints = [
        ('name_project_unique',
         'unique(name, project_temp_id)',
         'Le nom de la tâche doit être unique par projet!')
    ]

    @api.constrains('planned_hours')
    def _check_planned_hours(self):
        """Vérifie que les heures prévues sont positives."""
        for task in self:
            if task.planned_hours < 0:
                raise ValidationError(
                    _("Les heures prévues doivent être positives ou nulles.")
                )

    def name_get(self):
        """Affichage personnalisé avec le projet."""
        result = []
        for task in self:
            if task.project_temp_id:
                name = f"[{task.project_temp_id.name}] {task.name}"
            else:
                name = task.name
            result.append((task.id, name))
        return result
