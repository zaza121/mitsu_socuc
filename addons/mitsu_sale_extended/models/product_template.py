from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    temp_task_ids = fields.Many2many(
        'mitsu_sale.project_temp_task',
        'product_2_projectpt_rel',
        'product_id', 'template_id',
        string='Tâches modèles',
        help='Tâches qui seront créées automatiquement lors de la vente de ce produit'
    )

    temp_task_count = fields.Integer(
        string='Nb. Tâches',
        compute='_compute_temp_task_count',
        store=True
    )

    @api.depends('temp_task_ids')
    def _compute_temp_task_count(self):
        """Compte le nombre de tâches modèles."""
        for product in self:
            product.temp_task_count = len(product.temp_task_ids)

    def action_view_temp_tasks(self):
        """Action pour voir les tâches modèles du produit."""
        self.ensure_one()
        return {
            'name': _('Tâches modèles'),
            'type': 'ir.actions.act_window',
            'res_model': 'mitsu_sale.project_temp_task',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.temp_task_ids.ids)],
            'context': {'default_product_temp_ids': [(6, 0, [self.id])]},
        }
