{
    'name': "Project Intercompany Sync",
    'summary': "Synchronisation des tâches, temps alloué, planning et feuilles de temps entre les sociétés mères et sous-traitantes.",
    'version': '1.0',
    'category': 'Project/Timesheets',
    
    # Modules obligatoires
    'depends': [
        'base',
        'project',
        'hr_timesheet',  # Pour planned_hours et feuilles de temps
        'sale_project',  # Pour product_id (si utilisé)
        'planning',      # Pour planning.slot
    ],
    
    # Fichiers de données
    'data': [
        # --- Sécurité (Doit être chargé en premier !) ---
        'security/security.xml',
        'security/ir.model.access.csv',
        
        # --- Vues de Configuration ---
        'views/res_company_views.xml', # AJOUTÉ : POUR LA CASE 'Est un Sous-traitant'
        
        # --- Vues Projet & Tâche ---
        'views/project_task_views.xml',
        'views/project_task_actions.xml', # AJOUTÉ : POUR L'ACTION 'Synchroniser maintenant' (si créé)
        
        # --- Vues Planning ---
        'views/planning_slot_views.xml', # AJOUTÉ
        
        # --- Tâches Planifiées (CRON) ---
        'data/ir_cron_data.xml',
    ],
    
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}