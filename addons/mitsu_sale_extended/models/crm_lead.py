from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    distribution_id = fields.Many2one(
        'account.analytic.distribution.model',
        string='Modèle analytique',
        help='Modèle de distribution analytique qui sera appliqué aux devis/commandes'
    )
    account_id = fields.Many2one(
        'account.analytic.account',
        string='Compte analytique',
        help='Compte analytique principal pour cette opportunité'
    )

    def _prepare_opportunity_quotation_context(self):
        """
        Préparation du contexte pour la création de devis depuis l'opportunité.
        Transmet le modèle de distribution analytique.
        """
        ctx = dict(super()._prepare_opportunity_quotation_context() or {})

        if self.distribution_id:
            ctx['default_force_distribution_id'] = self.distribution_id.id
            _logger.info(
                "Distribution analytique %s appliquée au devis de l'opportunité %s",
                self.distribution_id.name, self.name
            )

        return ctx

    @api.onchange('account_id')
    def _onchange_account_id(self):
        """
        Si un compte analytique est sélectionné, proposer les modèles compatibles.
        """
        if self.account_id:
            # Rechercher les modèles contenant ce compte analytique
            models_ = self.env['account.analytic.distribution.model'].search([])
            # analytic_distribution est stocké en JSON/dict: keys sont des str d'ids
            compatible = models_.filtered(
                lambda m: m.analytic_distribution and str(self.account_id.id) in m.analytic_distribution.keys()
            )

            if compatible:
                return {
                    'domain': {
                        'distribution_id': [('id', 'in', compatible.ids)]
                    }
                }
