#-*- coding: utf-8 -*-
{
    'name': "Logique Avancée de Projet Template",
    'version': '18.0.1.0.0',
    'summary': 'Implémentation de projets templates, liens produits dans les tâches, restrictions financières et logique complexe de création depuis une commande.',
    'depends': ['project', 'sale_project', 'account', 'hr_expense'],
    'data': [
        'security/ir.model.access.csv',
        'security/project_security_rules.xml',
        'views/project_views.xml',
        'views/project_task_views.xml',
    ],
    'installable': True,
    'license': 'LGPL-3',
}