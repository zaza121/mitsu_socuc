from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class PlanningRole(models.Model):
    _inherit = 'planning.role'

    cost_ids = fields.One2many(
        'mitsu_sale.cost_role_line',
        'role_id',
        string='Lignes de coût',
        help='Définir les coûts par unité de mesure pour ce rôle'
    )

    cost_count = fields.Integer(
        string='Nombre de coûts',
        compute='_compute_cost_count',
        store=True
    )

    @api.depends('cost_ids')
    def _compute_cost_count(self):
        """Compte le nombre de lignes de coût pour l'affichage."""
        for role in self:
            role.cost_count = len(role.cost_ids)

    @api.constrains('cost_ids')
    def _check_unique_uom_per_role(self):
        """Vérifie qu'il n'y a pas de doublons d'unité de mesure par rôle."""
        for role in self:
            uoms = role.cost_ids.mapped('uom_id')
            if len(uoms) != len(set(uoms.ids)):
                raise ValidationError(
                    _("Un rôle ne peut avoir qu'un seul coût par unité de mesure.")
                )


class CostRoleLine(models.Model):
    _name = "mitsu_sale.cost_role_line"
    _description = "Coût par rôle et unité de mesure"
    _order = "role_id, uom_id"

    role_id = fields.Many2one(
        'planning.role',
        string='Rôle',
        required=True,
        ondelete='cascade',
        index=True
    )
    uom_id = fields.Many2one(
        'uom.uom',
        string='Unité de mesure',
        required=True,
        index=True
    )
    amount = fields.Float(
        string='Taux',
        required=True,
        digits='Product Price',
        help='Coût ou prix par unité'
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Devise',
        default=lambda self: self.env.company.currency_id,
        required=True
    )

    _sql_constraints = [
        ('unique_role_uom',
         'unique(role_id, uom_id)',
         'Un rôle ne peut avoir qu\'un seul taux par unité de mesure!')
    ]

    @api.constrains('amount')
    def _check_amount(self):
        """Vérifie que le montant est positif."""
        for line in self:
            if line.amount < 0:
                raise ValidationError(
                    _("Le taux doit être positif ou nul.")
                )

    def name_get(self):
        """Affichage personnalisé."""
        result = []
        for line in self:
            symbol = line.currency_id.symbol if line.currency_id else ''
            name = f"{line.role_id.name} - {line.uom_id.name}: {line.amount:.2f} {symbol}"
            result.append((line.id, name))
        return result
