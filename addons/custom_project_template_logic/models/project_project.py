# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

# 1. Ajout du drapeau Template
class ProjectProject(models.Model):
    _inherit = 'project.project'
    
    is_template = fields.Boolean(
        string="Est un Modèle (Template)",
        help="Si coché, ce projet ne peut pas recevoir de transactions financières (factures ou notes de frais)."
    )

# 2. Ajout du champ Produit dans la Tâche
class ProjectTask(models.Model):
    _inherit = 'project.task'
    
    product_id = fields.Many2one(
        'product.product',
        string="Produit lié (Template)",
        help="Produit à rechercher dans la commande de vente lors du clonage du projet modèle."
    )

# 3. Restriction : Blocage des factures (Achat et Vente) sur les Templates
class AccountMove(models.Model):
    _inherit = 'account.move'
    
    @api.constrains('invoice_line_ids', 'move_type')
    def _check_template_project_accounting(self):
        for move in self:
            if move.move_type in ('in_invoice', 'out_invoice'):
                for line in move.invoice_line_ids:
                    if line.analytic_distribution:
                        # Recherche du projet lié via le compte analytique
                        analytic_account_ids = [int(k) for k in line.analytic_distribution.keys()]
                        projects = self.env['project.project'].search([
                            ('analytic_account_id', 'in', analytic_account_ids),
                            ('is_template', '=', True)
                        ], limit=1)
                        
                        if projects:
                            raise UserError(_(
                                "Impossible de renseigner des factures d'achat ou de vente sur un projet modèle (%s)."
                            ) % projects.name)

# 4. Restriction : Blocage des notes de frais sur les Templates
class HrExpense(models.Model):
    _inherit = 'hr.expense'
    
    @api.constrains('project_id')
    def _check_template_project_expense(self):
        for expense in self:
            if expense.project_id and expense.project_id.is_template:
                raise UserError(_(
                    "Impossible de renseigner des notes de frais sur un projet modèle (%s)."
                ) % expense.project_id.name)