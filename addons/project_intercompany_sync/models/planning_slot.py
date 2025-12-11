from odoo import api, fields, models
import logging

_logger = logging.getLogger(__name__)

class PlanningSlot(models.Model):
    _inherit = "planning.slot"

    # CHAMPS MODIFIÉS : Ajout de readonly=True
    mirror_slot_id = fields.Many2one("planning.slot", string="Créneau miroir", readonly=True)
    origin_slot_id = fields.Many2one("planning.slot", string="Créneau d'origine", readonly=True)
    
    # CHAMPS DE LIAISON (Relatif à la tâche mère)
    mirrored_company_id = fields.Many2one(
        "res.company", string="Société miroir", related="task_id.mirrored_company_id", store=True, readonly=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        slots = super().create(vals_list)
        # La synchronisation immédiate (A -> B) est conservée ici
        for slot in slots:
            try:
                slot.sudo()._create_or_update_mirror_slot()
            except Exception:
                _logger.exception("Échec création/mise à jour créneau miroir pour planning.slot %s", slot.id)
        return slots

    def write(self, vals):
        res = super().write(vals)
        # La synchronisation immédiate (A -> B) est conservée ici
        if not self.env.context.get("skip_mirror_sync"):
            for slot in self:
                try:
                    slot.sudo()._create_or_update_mirror_slot()
                except Exception:
                    _logger.exception("Échec write création/mise à jour créneau miroir pour planning.slot %s", slot.id)
        return res

    def _create_or_update_mirror_slot(self):
        for slot in self:
            task = slot.task_id
            # On vérifie si la synchro est active sur la tâche
            if not task or not task.mirrored_company_id:
                continue
            mirror_company = task.mirrored_company_id
            if slot.company_id == mirror_company:
                continue
            mirror_task = task.mirror_task_id
            if not mirror_task:
                continue

            # Environnement pour création dans la société miroir
            mirror_env = self.env["planning.slot"].with_company(mirror_company).sudo()

            # NOTE : On ne synchronise PAS l'employé/utilisateur car ils sont locaux à la Société A.
            # L'employé/utilisateur B sera assigné sur le créneau miroir B.
            vals = {
                "start_datetime": slot.start_datetime,
                "end_datetime": slot.end_datetime,
                "allocated_hours": slot.allocated_hours,
                "user_id": False,  # Important : Laisser vide pour que B puisse assigner
                "employee_id": False, # Important : Laisser vide pour que B puisse assigner
                "task_id": mirror_task.id,
                "company_id": mirror_company.id,
                "origin_slot_id": slot.id,
            }

            if slot.mirror_slot_id:
                try:
                    slot.mirror_slot_id.with_context(skip_mirror_sync=True).sudo().write(vals)
                except Exception:
                    _logger.exception("Impossible de mettre à jour le mirror_slot %s", slot.mirror_slot_id.id)
            else:
                try:
                    mirror_slot = mirror_env.create(vals)
                    slot.sudo().write({"mirror_slot_id": mirror_slot.id})
                except Exception:
                    _logger.exception("Impossible de créer le créneau miroir pour planning.slot %s", slot.id)

    def unlink(self):
        mirrors = self.mapped("mirror_slot_id")
        res = super().unlink()
        if mirrors:
            try:
                mirrors.with_context(skip_mirror_sync=True).sudo().unlink()
            except Exception:
                _logger.exception("Impossible de supprimer les créneaux miroir lors de la suppression.")
        return res