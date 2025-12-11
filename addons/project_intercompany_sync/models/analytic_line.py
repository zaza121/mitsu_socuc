from odoo import api, models, _, fields
from odoo.exceptions import AccessError
import logging

_logger = logging.getLogger(__name__)

class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    # NOUVEAUX CHAMPS POUR LA SYNCHRONISATION CRON (B -> A)
    
    origin_analytic_line_id = fields.Many2one(
        'account.analytic.line', 
        string="Feuille de Temps d'Origine", 
        readonly=True,
        help="Référence à la feuille de temps originale dans la société miroir (B)."
    )
    
    synced_to_origin = fields.Boolean(
        string="Synchronisé vers l'Origine", 
        default=False,
        help="Indique si cette feuille de temps de la tâche miroir (B) a été copiée vers la tâche d'origine (A)."
    )
    
    # ----------------------------------------------------
    # MODIFICATION DE LA LOGIQUE EXISTANTE (CRÉATION)
    # ----------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        current_user = self.env.user
        
        # Le flag 'skip_mirror_sync' est utilisé par notre code CRON dans project_task.py
        # pour créer la ligne miroir (FT A) sans déclencher la vérification du planning.
        skip_planning_check = self.env.context.get("skip_mirror_sync") or self.env.context.get("skip_planning_check")

        for vals in vals_list:
            task_id = vals.get("task_id")
            if not task_id or skip_planning_check:
                continue

            task = self.env["project.task"].browse(task_id)
            if not task:
                continue

            # Vérification du planning existante
            slot_domain = [
                ("task_id", "=", task.id),
                "|",
                ("user_id", "=", current_user.id),
                ("employee_id.user_id", "=", current_user.id),
            ]
            slot = self.env["planning.slot"].sudo().search(slot_domain, limit=1)
            
            # Application de la règle du planning, sauf si le CRON est en train de créer la ligne miroir.
            if not slot:
                raise AccessError(
                    _("Vous ne pouvez saisir du temps que si vous avez été planifié sur cette tâche.")
                )

        lines = super().create(vals_list)

        # L'ancienne logique de synchronisation immédiate (_sync_mirror_timesheet) est retirée.
        # Le tracking est désormais géré par le CRON dans project_task.py.
        
        return lines

    # Les méthodes _sync_mirror_timesheet et _prepare_mirror_vals existantes sont retirées
    # car elles sont remplacées par la logique de remontée centralisée du CRON.