from odoo import fields, models, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class ProjectTask(models.Model):
    _inherit = 'project.task'
    
    # CHAMPS DE LIAISON (Assurez-vous qu'ils existent)
    mirrored_company_id = fields.Many2one(
        'res.company', 
        string='Société Miroir',
        domain="[('id', '!=', company_id), ('is_subcontractor', '=', True)]", 
        help="Sélectionnez la société vers laquelle cette tâche doit être miroitée."
    )
    
    mirror_task_id = fields.Many2one(
        'project.task',
        string='Tâche Miroir',
        readonly=True, 
        help="Référence à la tâche miroir chez la société sous-traitante."
    )
    
    origin_task_id = fields.Many2one(
        'project.task',
        string="Tâche d'Origine",
        readonly=True, 
        help="Référence à la tâche originale chez la société donneuse d'ordre."
    )

    # ----------------------------------------------------
    # MÉTHODES DÉCLENCHÉES PAR L'UTILISATEUR
    # ----------------------------------------------------

    def action_sync_intercompany_now(self):
        """Action pour le bouton 'Synchroniser maintenant'."""
        self.ensure_one()
        self.sync_intercompany_tasks(self.ids) 
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Synchronisation réussie'),
                'message': _('La tâche a été synchronisée avec la société miroir.'),
                'sticky': False,
            }
        }

    # ----------------------------------------------------
    # MÉTHODE DE SYNCHRONISATION (CRON et Bouton)
    # ----------------------------------------------------

    @api.model
    def sync_intercompany_tasks(self, task_ids=None):
        """
        Gère la remontée (B -> A) et la poussée (A -> B) des données.
        """
        
        # Vérification de la disponibilité des champs et des modèles
        planned_hours_available = 'planned_hours' in self.env['project.task']._fields
        product_id_available = 'product_id' in self.env['project.task']._fields
        
        analytic_line_available = ('account.analytic.line' in self.env and 
                                   'synced_to_origin' in self.env['account.analytic.line']._fields)
        
        if not analytic_line_available:
            _logger.warning("Le modèle account.analytic.line ou les champs de synchronisation sont manquants. La remontée des FT est ignorée.")
            
        # --- 1. Remontée : Miroir (Sous-traitant B) vers Original (Donneur d'ordre A) ---
        
        # On recherche toutes les tâches qui sont des miroirs (celles qui ont une 'origin_task_id')
        mirrors = self.sudo().search([('origin_task_id', '!=', False)])
        
        for mirror in mirrors:
            original_task = mirror.origin_task_id
            if not original_task:
                continue

            # 1a. Synchronisation du statut
            if original_task.stage_id != mirror.stage_id:
                original_task.sudo().write({'stage_id': mirror.stage_id.id})
            
            # 1b. Synchronisation des Feuilles de Temps (Timesheets)
            if analytic_line_available:
                try:
                    # Recherche les FT non synchronisées dans la Société B (mirror.company_id)
                    mirror_timesheets = self.env['account.analytic.line'].sudo().with_company(mirror.company_id.id).search([
                        ('task_id', '=', mirror.id),         
                        ('synced_to_origin', '=', False),  
                    ], order='create_date desc')

                    last_timesheet_user = False 

                    for timesheet in mirror_timesheets:
                        user_name = timesheet.user_id.name if timesheet.user_id else timesheet.employee_id.name if timesheet.employee_id else _('Sous-traitant B')

                        vals = {
                            'name': f"Temps Sous-traitance (Par {user_name}, {timesheet.unit_amount}h) : {timesheet.name}",
                            'date': timesheet.date,
                            'unit_amount': timesheet.unit_amount, 
                            'task_id': original_task.id, 
                            'project_id': original_task.project_id.id, 
                            'company_id': original_task.company_id.id, 
                            'origin_analytic_line_id': timesheet.id,
                            'employee_id': False, 
                        }
                        # Ajout conditionnel du produit pour la FT
                        if product_id_available and original_task.product_id:
                            vals['product_id'] = original_task.product_id.id

                        # Créer la feuille de temps dans la Société A (original_task.company_id)
                        new_timesheet = self.env['account.analytic.line'].with_context(skip_planning_check=True, skip_mirror_sync=True).sudo().with_company(original_task.company_id.id).create(vals)
                        
                        # Marquer l'enregistrement miroir (B) comme synchronisé
                        timesheet.sudo().write({
                            'synced_to_origin': True,
                        })

                        if timesheet.user_id:
                            last_timesheet_user = timesheet.user_id.id

                    # 1c. Assignation de l'utilisateur sur la tâche A
                    if last_timesheet_user:
                        user_to_assign = self.env['res.users'].sudo().browse(last_timesheet_user)
                        
                        if user_to_assign.exists() and original_task.company_id.id in user_to_assign.company_ids.ids:
                            current_users = original_task.user_ids.ids
                            if last_timesheet_user not in current_users:
                                original_task.sudo().write({'user_ids': [(4, last_timesheet_user)]})

                except Exception as e:
                    _logger.error("Échec critique lors de la remontée des FT pour la tâche miroir %s : %s", mirror.name, e)

                            
        # --- 2. Poussée : Original (Donneur d'ordre A) vers Miroir (Sous-traitant B) ---
        
        if task_ids:
            originals = self.sudo().browse(task_ids)
        else:
            # Pour le CRON : cherche toutes les tâches A à synchroniser
            originals = self.sudo().search([
                ('mirrored_company_id', '!=', False),
                ('company_id', '!=', False),
            ])

        for task in originals:
            if task.mirrored_company_id == task.company_id:
                continue

            try:
                # --- GESTION DU PROJET MIROIR (simplifié) ---
                mirror_project_name = f"{task.project_id.name} (MIROIR)" if task.project_id else "Tâches Miroir Inter-Compagnies"
                
                mirror_project = self.env['project.project'].sudo().with_company(task.mirrored_company_id.id).search([
                    ('company_id', '=', task.mirrored_company_id.id),
                    ('name', '=', mirror_project_name)
                ], limit=1)
                
                if not mirror_project:
                    mirror_project = self.env['project.project'].sudo().with_company(task.mirrored_company_id.id).create({
                        'name': mirror_project_name,
                        'company_id': task.mirrored_company_id.id,
                        'allow_timesheets': True,
                    })
                
                # --- CRÉATION DE LA TÂCHE MIROIR ---
                
                if not task.mirror_task_id:
                    vals = {
                        'name': f"[MIRROR] {task.name}",
                        'company_id': task.mirrored_company_id.id,
                        'project_id': mirror_project.id,
                        'user_ids': [(5, 0, 0)],
                        'origin_task_id': task.id,
                        'stage_id': task.stage_id.id,
                    }
                    
                    if planned_hours_available:
                        vals['planned_hours'] = task.planned_hours
                    if product_id_available and task.product_id:
                        vals['product_id'] = task.product_id.id
                    
                    # Création en désactivant la synchro immédiate
                    mirror_task = self.with_context(skip_mirror_sync=True).sudo().with_company(task.mirrored_company_id.id).create(vals)
                    task.sudo().write({'mirror_task_id': mirror_task.id})
                
                # --- MISE À JOUR DE LA TÂCHE MIROIR ---
                
                elif task.mirror_task_id:
                    updates = {
                        'name': f"[MIRROR] {task.name}",
                        'description': task.description,
                    }
                    
                    if planned_hours_available:
                        updates['planned_hours'] = task.planned_hours
                    
                    if product_id_available and task.product_id and task.mirror_task_id.product_id != task.product_id:
                        updates['product_id'] = task.product_id.id
                    
                    # Mise à jour en désactivant la synchro immédiate
                    task.mirror_task_id.with_context(skip_mirror_sync=True).sudo().write(updates)

            except Exception as e:
                _logger.error("Échec critique lors de la poussée vers la tâche miroir pour %s : %s", task.name, e)

        return True