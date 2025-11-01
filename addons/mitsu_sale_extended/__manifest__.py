{
    'name': "MITSU Sale Extended",
    'version': "18.0.1.0.3",
    'category': 'Sales/CRM',
    'summary': "Extensions CRM, Sales & Project pour MITSUKI",
    'description': """
    Ce module étend les fonctionnalités des ventes et projets :
    - Ajout de distributions analytiques CRM → Vente
    - Gestion de rôles et coûts associés dans la planification
    - Tâches automatiques liées aux produits et projets
    - Optimisations de performance et gestion d'erreurs robuste
    """,
    'author': "MITSUKI TECHNOLOGIE CONSEIL",
    'maintainer': "MITSUKI TECHNOLOGIE CONSEIL",
    'website': "https://www.mitsuki-technologie.com",
    'depends': [
        'sale',
        'crm',
        'sale_crm',
        'planning',
        'sale_project',
        'account',
        'analytic_distribution',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/crm_lead_views.xml',
        'views/sale_order_views.xml',
        'views/planning_role_views.xml',
        'views/analytic_distribution_model_views.xml',
        'views/project_project_views.xml',
        'views/project_temp_task_views.xml',
        'views/product_template_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': "AGPL-3",
    'installable': True,
    'application': False,
}
