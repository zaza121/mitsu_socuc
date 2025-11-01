from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    role_id = fields.Many2one(
        'planning.role',
        string='Rôle',
        help='Rôle de planification associé à cette ligne'
    )
    force_modele_id = fields.Many2one(
        'account.analytic.distribution.model',
        string='Modèle analytique spécifique',
        help='Modèle analytique spécifique pour cette ligne (prioritaire sur le modèle de la commande)'
    )

    @api.onchange('role_id', 'product_uom')
    def _onchange_role_id(self):
        """
        Met à jour le prix unitaire en fonction du coût du rôle.
        CORRECTION: Gestion robuste avec logging et validation.
        """
        if not (self.role_id and self.product_uom):
            return

        try:
            # Rechercher le coût correspondant à l'unité de mesure
            cost_line = self.role_id.cost_ids.filtered(
                lambda l: l.uom_id == self.product_uom
            )

            if cost_line:
                # Prendre le premier si plusieurs (ne devrait pas arriver avec contrainte)
                self.price_unit = cost_line[0].amount

                _logger.info(
                    "Prix unitaire mis à jour: %s pour le rôle %s avec l'unité %s",
                    cost_line[0].amount, self.role_id.name, self.product_uom.name
                )
            else:
                # Avertir si aucun coût n'est défini
                _logger.warning(
                    "Aucun coût défini pour le rôle %s avec l'unité %s",
                    self.role_id.name if self.role_id else 'N/A', 
                    self.product_uom.name if self.product_uom else 'N/A'
                )

        except Exception as e:
            _logger.error("Erreur lors de la mise à jour du prix via le rôle: %s", str(e))

    @api.onchange('force_modele_id')
    def _onchange_force_modele_id(self):
        """
        Applique la distribution analytique du modèle choisi.
        CORRECTION: Validation et logging.
        """
        if self.force_modele_id:
            if self.force_modele_id.analytic_distribution:
                self.analytic_distribution = dict(self.force_modele_id.analytic_distribution)
                _logger.info(
                    "Distribution analytique appliquée depuis le modèle %s",
                    self.force_modele_id.name
                )
            else:
                # vider éventuellement la distribution si pas définie
                self.analytic_distribution = {}
                _logger.warning(
                    "Le modèle %s n'a pas de distribution analytique définie",
                    self.force_modele_id.name
                )

    @api.depends('order_id.force_distribution_id')
    def _compute_analytic_distribution(self):
        """
        Priorise le modèle analytique forcé sur la commande.
        CORRECTION: Appel du super en premier pour garder le comportement parent par défaut,
        puis application du forcing si besoin.
        """
        super(SaleOrderLine, self)._compute_analytic_distribution()
        for line in self:
            # Si un modèle est forcé au niveau commande et pas de modèle spécifique sur la ligne
            if line.order_id and line.order_id.force_distribution_id and not line.force_modele_id:
                line.force_modele_id = line.order_id.force_distribution_id
                if line.order_id.force_distribution_id.analytic_distribution:
                    line.analytic_distribution = dict(line.order_id.force_distribution_id.analytic_distribution)

    def _timesheet_create_project_prepare_values(self):
        """
        Ajout automatique des plans analytiques dans les projets créés.
        CORRECTION: Gestion robuste des clés de distribution et validation.
        """
        vals = super(SaleOrderLine, self)._timesheet_create_project_prepare_values()

        if not self.analytic_distribution:
            return vals

        try:
            # Récupérer les IDs des comptes analytiques depuis la distribution
            account_ids = []
            for key in self.analytic_distribution.keys():
                try:
                    account_ids.append(int(key))
                except (ValueError, TypeError) as e:
                    _logger.warning("Clé de distribution invalide: %s - %s", key, str(e))
                    continue

            if not account_ids:
                return vals

            # Charger les comptes analytiques
            accounts = self.env['account.analytic.account'].browse(account_ids)

            # Créer le mapping plan → compte
            plan_map = {}
            for account in accounts:
                if account.plan_id:
                    field_name = f"x_plan{account.plan_id.id}_id"
                    plan_map[field_name] = account.id

            if plan_map:
                vals.update(plan_map)
                _logger.info("Plans analytiques ajoutés au projet: %s", list(plan_map.keys()))

        except Exception as e:
            _logger.error("Erreur lors de l'ajout des plans analytiques au projet: %s", str(e))

        return vals

    def _timesheet_service_generation(self):
        """
        Création automatique de tâches selon les modèles de produit.
        CORRECTION: Gestion d'erreurs robuste, logging et optimisation.
        """
        res = super(SaleOrderLine, self)._timesheet_service_generation()

        # Filtrer les lignes concernées
        lines_to_process = self.filtered(
            lambda l: l.product_id and l.product_id.service_tracking == 'project_only'
            and l.product_id.temp_task_ids
        )

        if not lines_to_process:
            return res

        task_model = self.env['project.task']
        created_tasks = []

        for line in lines_to_process:
            if not line.project_id:
                _logger.warning(
                    "Aucun projet défini pour la ligne %s - Création de tâches ignorée", line.id
                )
                continue

            try:
                # Récupérer les tâches modèles triées par séquence
                temp_tasks = line.product_id.temp_task_ids.sorted('sequence')

                for temp_task in temp_tasks:
                    # Préparer les valeurs de création
                    task_vals = {
                        'name': temp_task.name,
                        'partner_id': line.order_id.partner_id.id if line.order_id.partner_id else False,
                        'description': temp_task.description or line.name,
                        'project_id': line.project_id.id,
                        'sale_line_id': line.id,
                        'sale_order_id': line.order_id.id if line.order_id else False,
                        'company_id': line.company_id.id if line.company_id else self.env.company.id,
                    }

                    # Ajouter les champs optionnels si définis
                    if temp_task.planned_hours:
                        task_vals['planned_hours'] = temp_task.planned_hours

                    if temp_task.user_ids:
                        task_vals['user_ids'] = [(6, 0, temp_task.user_ids.ids)]
                    else:
                        task_vals['user_ids'] = False

                    if temp_task.tag_ids:
                        task_vals['tag_ids'] = [(6, 0, temp_task.tag_ids.ids)]

                    # Créer la tâche
                    task = task_model.create(task_vals)
                    created_tasks.append(task)

                    _logger.info("Tâche créée: %s pour le projet %s", task.name, line.project_id.name)

            except Exception as e:
                _logger.error("Erreur lors de la création des tâches pour la ligne %s: %s", line.id, str(e))
                # Ne pas bloquer le processus pour les autres lignes
                continue

        if created_tasks:
            _logger.info("Total de %s tâches créées depuis les modèles", len(created_tasks))

        return res
