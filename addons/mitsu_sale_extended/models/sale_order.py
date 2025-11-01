from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    force_distribution_id = fields.Many2one(
        'account.analytic.distribution.model',
        string='Modèle analytique forcé',
        help='Force l\'application de ce modèle analytique à toutes les lignes'
    )

    @api.onchange('force_distribution_id')
    def _onchange_force_distribution_id(self):
        """
        Applique le modèle analytique à toutes les lignes existantes.
        """
        if self.force_distribution_id and self.order_line:
            for line in self.order_line:
                line.force_modele_id = self.force_distribution_id
                # copy dict if present
                if self.force_distribution_id.analytic_distribution:
                    line.analytic_distribution = dict(self.force_distribution_id.analytic_distribution)
                else:
                    line.analytic_distribution = {}
            _logger.info(
                "Modèle analytique %s appliqué à %s lignes de la commande %s",
                self.force_distribution_id.name, len(self.order_line), self.name
            )
