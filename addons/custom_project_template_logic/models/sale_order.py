# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        so_products = self.order_line.mapped('product_id')
        
        for line in self.order_line:
            template_project = line.product_id.project_id
            
            if template_project and template_project.is_template:
                
                # --- VÉRIFICATION DE BLOCAGE ---
                template_task_products = template_project.task_ids.mapped('product_id')
                template_task_products = template_task_products.filtered(lambda p: p)
                
                if template_task_products:
                    required_products_not_in_so = template_task_products - so_products
                    
                    if required_products_not_in_so:
                        product_names = ', '.join(required_products_not_in_so.mapped('name'))
                        raise UserError(_(
                            "Création de projet bloquée ! Le projet modèle '%s' requiert les produits suivants dans le bon de commande : %s."
                        ) % (template_project.name, product_names))
                        
                # --- CRÉATION et CLONAGE ---
                project_vals = {
                    'name': self.name,
                    'analytic_account_id': self.analytic_account_id.id,
                    'partner_id': self.partner_id.id,
                    'user_id': self.user_id.id,
                    'is_template': False,
                }
                
                new_project = template_project.copy(project_vals)
                
                # Ajout de l'utilisateur courant comme follower (visibilité)
                new_project.message_subscribe(partner_ids=self.env.user.partner_id.ids)
                
                # --- LIAISON TÂCHE <-> ARTICLE DE COMMANDE ---
                for new_task in new_project.task_ids:
                    if new_task.product_id:
                        so_line = self.order_line.filtered(
                            lambda l: l.product_id.id == new_task.product_id.id
                        )
                        if so_line:
                            new_task.sale_line_id = so_line[0].id
                
                # Empêche la création standard Odoo après le super
                line.product_id.project_id = False
                
        return super().action_confirm()