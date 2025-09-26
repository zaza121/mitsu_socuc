from odoo import models

class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_project_for_order(self):
        """Récupère le projet lié à la commande (via analytic_account_id)."""
        self.ensure_one()
        if self.analytic_account_id:
            return self.analytic_account_id.project_ids[:1]
        return self.env['project.project']

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            project = order._get_project_for_order()
            if not project:
                continue

            for line in order.order_line:
                tmpl_task = line.product_id.product_tmpl_id.task_template_id
                if not tmpl_task:
                    continue

                # Chercher tâche déjà copiée (fiable via template_task_id)
                task = self.env['project.task'].search([
                    ('project_id', '=', project.id),
                    ('template_task_id', '=', tmpl_task.id),
                ], limit=1)

                if not task:
                    # Copier la tâche du template dans le projet
                    vals = {
                        'project_id': project.id,
                        'template_task_id': tmpl_task.id,
                        'sale_line_id': line.id,
                        'product_id': line.product_id.id,
                    }
                    task = tmpl_task.copy(default=vals)
                else:
                    task.sudo().write({
                        'sale_line_id': line.id,
                        'product_id': line.product_id.id,
                    })

        return res

    def action_view_linked_tasks(self):
        """ Affiche les tâches liées à cette commande """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tâches liées',
            'res_model': 'project.task',
            'view_mode': 'tree,form',
            'domain': [('sale_line_id.order_id', '=', self.id)],
        }
