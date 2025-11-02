from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)

class ProjectTask(models.Model):
    _inherit = "project.task"

    mirror_task_id = fields.Many2one("project.task", string="Tâche miroir")
    origin_task_id = fields.Many2one("project.task", string="Tâche d'origine")
    mirrored_company_id = fields.Many2one(
        "res.company",
        string="Société miroir",
        domain="[('is_subcontractor', '=', True)]",
        help="Société sous-traitante avec laquelle synchroniser la tâche.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        tasks = super().create(vals_list)
        for task in tasks:
            # Toujours exécuter en sudo pour permettre la création dans la société miroir
            try:
                task.sudo()._create_or_update_mirror()
            except Exception:
                _logger.exception("Échec de création/mise à jour de la tâche miroir pour %s", task.id)
        return tasks

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get("skip_mirror_sync"):
            for task in self:
                try:
                    task.sudo()._create_or_update_mirror()
                except Exception:
                    _logger.exception("Échec de création/mise à jour de la tâche miroir lors du write pour %s", task.id)
        return res

    def _create_or_update_mirror(self):
        for task in self:
            mirror_company = task.mirrored_company_id
            if not mirror_company or mirror_company == task.company_id:
                continue

            # Utiliser l'environnement avec la société miroir et en sudo
            mirror_env = self.env["project.task"].with_company(mirror_company).sudo()

            if task.mirror_task_id:
                vals = {"name": task.name, "description": task.description or ""}
                try:
                    # Écrire sans déclencher la synchronisation récursive
                    task.mirror_task_id.with_context(skip_mirror_sync=True).sudo().write(vals)
                except Exception:
                    _logger.exception("Impossible de mettre à jour la tâche miroir %s", bool(task.mirror_task_id))
            else:
                vals = {
                    "name": task.name,
                    "description": task.description or "",
                    "project_id": task.project_id.id if task.project_id else False,
                    "company_id": mirror_company.id,
                    "origin_task_id": task.id,
                }
                try:
                    # Créer la tâche miroir dans l'environnement mirror (societé miroir)
                    mirror_task = mirror_env.create(vals)
                    task.sudo().write({"mirror_task_id": mirror_task.id})
                except Exception:
                    _logger.exception("Impossible de créer la tâche miroir pour la tâche %s", task.id)

    @api.model
    def _cron_sync_intercompany(self):
        tasks = self.search([("mirrored_company_id", "!=", False)])
        for task in tasks:
            try:
                task.sudo()._create_or_update_mirror()
            except Exception:
                _logger.exception("Erreur lors de la synchronisation cron pour la tâche %s", task.id)
        # Synchroniser aussi les créneaux de planning
        try:
            self.env["planning.slot"].sudo().search([])._create_or_update_mirror_slot()
        except Exception:
            _logger.exception("Erreur lors de la synchronisation des planning slots via cron.")
        _logger.info("✅ Synchronisation inter-sociétés automatique exécutée.")

    def action_sync_intercompany_now(self):
        for task in self:
            try:
                task.sudo()._create_or_update_mirror()
            except Exception:
                _logger.exception("Erreur lors de la synchronisation manuelle pour la tâche %s", task.id)

        planning_slots = self.env["planning.slot"].search([("task_id", "in", self.ids)])
        try:
            planning_slots.sudo()._create_or_update_mirror_slot()
        except Exception:
            _logger.exception("Erreur lors de la synchronisation manuelle des planning slots pour les tâches %s", self.ids)

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Synchronisation terminée"),
                "message": _("%s tâche(s) et leurs plannings ont été synchronisés.") % len(self),
                "type": "success",
            },
        }
