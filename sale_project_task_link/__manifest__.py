{
    "name": "Sale Project Task Link",
    "version": "18.0.1.0.0",
    "summary": "Lie automatiquement les lignes de commande aux tâches du projet créé depuis un template",
    "category": "Sales/Project",
    "author": "Custom Dev",
    "depends": ["sale_project", "project", "sale"],
    "data": [
        "security/ir.model.access.csv",
        "views/product_template_views.xml",
        "views/project_task_views.xml",
        "views/sale_order_views.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
