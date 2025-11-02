from odoo import api, models, _, fields
from odoo.exceptions import AccessError
import logging

_logger = logging.getLogger(__name__)

class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    @api.model_create_multi
    def create(self, vals_list):
        current_user = self.env.user
        for vals in vals_list:
            task_id = vals.get("task_id")
            if not task_id:
                continue

            task = self.env["project.task"].browse(task_id)
            if not task:
                continue

            slot_domain = [
                ("task_id", "=", task.id),
                "|",
                ("user_id", "=", current_user.id),
                ("employee_id.user_id", "=", current_user.id),
            ]
            slot = self.env["planning.slot"].sudo().search(slot_domain, limit=1)
            if not slot:
                raise AccessError(
                    _("Vous ne pouvez saisir du temps que si vous avez été planifié sur cette tâche.")
                )

        lines = super().create(vals_list)

        for line in lines:
            if not self.env.context.get("skip_mirror_sync"):
                try:
                    line.sudo()._sync_mirror_timesheet()
                except Exception:
                    _logger.exception("Erreur lors de la synchronisation des timesheets miroir pour la ligne %s", line.id)
        return lines

    def _sync_mirror_timesheet(self):
        for line in self:
            task = line.task_id
            if not task:
                continue
            target_task = task.mirror_task_id or task.origin_task_id
            if not target_task:
                continue
            if not target_task.company_id:
                # Sans société cible, ne pas créer la ligne miroir
                continue
            vals = line._prepare_mirror_vals(target_task)
            try:
                # Créer la ligne analytique sur la société cible en sudo et en évitant la récursion
                self.with_context(skip_mirror_sync=True).sudo().with_company(target_task.company_id).create(vals)
            except Exception:
                _logger.exception("Impossible de créer la ligne analytique miroir pour la ligne %s", line.id)

    def _prepare_mirror_vals(self, target_task):
        self.ensure_one()
        return {
            "name": self.name,
            "date": self.date,
            "unit_amount": self.unit_amount,
            "employee_id": self.employee_id.id if self.employee_id else False,
            "user_id": self.user_id.id if self.user_id else False,
            "project_id": target_task.project_id.id,
            "task_id": target_task.id,
            "company_id": target_task.company_id.id,
            "product_id": self.product_id.id if self.product_id else False,
            "account_id": target_task.project_id.analytic_account_id.id
            if target_task.project_id and target_task.project_id.analytic_account_id
            else False,
        }
