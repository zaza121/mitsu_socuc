from odoo import fields, models, api


class AccountAnalyticDistributionModel(models.Model):
    _inherit = 'account.analytic.distribution.model'

    name = fields.Char(
        string='Nom',
        required=True,
        translate=True,
        help='Nom du modèle de distribution analytique'
    )

    # Ajout d'un champ pour faciliter l'usage
    description = fields.Text(
        string='Description',
        help='Description détaillée du modèle de distribution'
    )

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Le nom du modèle doit être unique!')
    ]
