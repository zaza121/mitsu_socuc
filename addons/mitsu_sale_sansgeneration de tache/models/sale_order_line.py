# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    role_id = fields.Many2one(
        comodel_name="planning.role",
        string="Rôle de Planification",
        domain="[('|', ('company_id', '=', False), ('company_id', '=', company_id))]",
    )

    force_modele_id = fields.Many2one(
        comodel_name="account.analytic.distribution.model",
        string="Modèle Analytique (Ligne)",
    )

    @api.onchange("role_id", "product_uom", "product_uom_qty")
    def _onchange_role_id(self):
        """Met à jour le prix unitaire selon le rôle et l'UoM (compatible Odoo 18)."""
        for rec in self:
            if rec.role_id and rec.product_uom:
                # filtered_domain est plus performant et compatible Odoo 18+
                line = rec.role_id.price_ids.filtered_domain([
                    ("uom_id", "=", rec.product_uom.id)
                ])
                if line:
                    rec.price_unit = line[0].amount

    @api.onchange("force_modele_id")
    def _onchange_force_modele_id(self):
        for rec in self:
            rec.analytic_distribution = rec.force_modele_id.analytic_distribution or {}

    @api.depends(
        "order_id.partner_id",
        "product_id",
        "order_id.force_distribution_id",
    )
    def _compute_analytic_distribution(self):
        """Prend en compte le modèle forcé au niveau de l'en-tête si présent."""
        for record in self:
            # Par défaut, laisse Odoo gérer le calcul pour chaque record
            # Si l'en-tête force la distribution, on l'applique
            if record.order_id and record.order_id.force_distribution_id:
                model = record.order_id.force_distribution_id
                record.force_modele_id = model
                record.analytic_distribution = model.analytic_distribution
            else:
                # appelle la logique standard d'Odoo pour ce record
                # on collecte les records sans forçage et on appelle super sur eux
                pass

        # Appel super pour les cas sans modèle forcé
        without_distri = self.filtered(lambda r: not (r.order_id and r.order_id.force_distribution_id))
        if without_distri:
            super(SaleOrderLine, without_distri)._compute_analytic_distribution()

    def _timesheet_create_project_prepare_values(self):
        """Conserve le comportement standard (hook pour personnalisation future)."""
        return super()._timesheet_create_project_prepare_values()

    def _timesheet_service_generation(self):
        """Exécute la logique standard pour la génération de services/tâches."""
        return super()._timesheet_service_generation()

    def _update_project_analytic_distribution(self):
        """
        Ajoute le compte analytique du projet à la distribution si absent.
        Cette logique est appelée depuis write() pour éviter de modifier des données
        dans une contrainte.
        """
        for rec in self:
            if (
                rec.state not in ("draft", "cancel")
                and rec.project_id
                and rec.project_id.account_id
                and not rec.force_modele_id
            ):
                account = rec.project_id.account_id
                dist = rec.analytic_distribution or {}
                if str(account.id) not in dist:
                    rec.analytic_distribution = {**dist, str(account.id): 100}

    def write(self, vals):
        res = super().write(vals)
        # Si le projet, l'état ou la distribution a changé, on met à jour
        if any(k in vals for k in ("project_id", "state", "analytic_distribution")):
            self._update_project_analytic_distribution()
        return res
