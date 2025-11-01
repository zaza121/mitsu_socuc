from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class ProjectProject(models.Model):
    _inherit = 'project.project'

    temp_task_ids = fields.One2many(
        'mitsu_sale.project_temp_task',
        'project_temp_id',
        string='Tâches modèles',
        help='Tâches modèles définies pour ce projet'
    )

    temp_task_count = fields.Integer(
        string='Nb. Tâches modèles',
        compute='_compute_temp_task_count',
        store=True
    )

    @api.depends('temp_task_ids')
    def _compute_temp_task_count(self):
        """Compte le nombre de tâches modèles."""
        for project in self:
            project.temp_task_count = len(project.temp_task_ids)

    def _sync_template_tasks(self):
        """
        Synchronise automatiquement les tâches modèles avec les labels.
        Mise en oeuvre via write/create déclencheurs pour éviter un usage inapproprié de @api.constrains.
        """
        for project in self:
            if not project.label_tasks:
                # Si le champ label_tasks est vide, on supprime les temp_task qui ne sont plus pertinents ?
                # Ici on se contente de continuer.
                continue

            try:
                # Parser les labels (format: "Label1, Label2, Label3")
                labels = [
                    x.strip()
                    for x in project.label_tasks.split(",")
                    if x.strip()
                ]

                if not labels:
                    continue

                existing_names = project.temp_task_ids.mapped('name')

                # Supprimer les tâches obsolètes
                to_delete = project.temp_task_ids.filtered(
                    lambda t: t.name not in labels
                )
                if to_delete:
                    _logger.info(
                        "Suppression de %s tâches obsolètes du projet %s",
                        len(to_delete), project.name
                    )
                    # unlink en sudo si nécessaire pourrait être envisagé, mais on essaye normal
                    to_delete.unlink()

                # Créer les nouvelles tâches manquantes
                to_create = set(labels) - set(existing_names)
                if to_create:
                    _logger.info(
                        "Création de %s nouvelles tâches pour le projet %s",
                        len(to_create), project.name
                    )

                    for name in to_create:
                        self.env['mitsu_sale.project_temp_task'].create({
                            'name': name,
                            'project_temp_id': project.id
                        })

            except Exception as e:
                _logger.error(
                    "Erreur lors de la synchronisation des tâches pour le projet %s: %s",
                    project.name, str(e)
                )
                raise ValidationError(
                    _("Erreur de synchronisation des tâches: %s") % str(e)
                )

    # Déclencher la synchronisation quand label_tasks est modifié via write/create
    def write(self, vals):
        res = super().write(vals)
        if 'label_tasks' in vals:
            # appeler sur les enregistrements concernés
            self._sync_template_tasks()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        # Synchroniser les objets nouvellement créés si nécessaire
        records_to_sync = records.filtered(lambda r: r.label_tasks)
        if records_to_sync:
            records_to_sync._sync_template_tasks()
        return records

    def action_view_temp_tasks(self):
        """Action pour voir les tâches modèles du projet."""
        self.ensure_one()
        return {
            'name': _('Tâches modèles'),
            'type': 'ir.actions.act_window',
            'res_model': 'mitsu_sale.project_temp_task',
            'view_mode': 'tree,form',
            'domain': [('project_temp_id', '=', self.id)],
            'context': {'default_project_temp_id': self.id},
        }
