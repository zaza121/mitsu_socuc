{
    'name': 'Mitsu HR Equipe',
    'version': '1.1',
    'category': 'Human Resources',
    'summary': 'Gestion des équipes et intégration Planning/Projet/Tâches',
    'license': 'LGPL-3',  # Ajoutez cette ligne
    'depends': [
        'hr', 
        'planning', 
        'project'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_team_views.xml',
        'views/planning_views.xml',
        'views/project_views.xml',     
    ],
    'installable': True,
    'application': False,
}