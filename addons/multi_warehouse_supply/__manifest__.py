# -*- coding: utf-8 -*-
{
    'name': 'Multi Warehouse Supply',
    'version': '18.0.1.0.0',
    'summary': 'Wizard to create internal transfers from one source to many destinations',
    'description': """
Approvisionner plusieurs emplacements / entrepôts depuis un emplacement source.
Crée automatiquement les transferts internes (pickings + moves), avec options de regroupement et confirmation.
""",
    'author': 'Your Company',
    'website': 'https://yourcompany.example.com',
    'license': 'LGPL-3',
    'category': 'Inventory/Operations',
    'depends': [
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/multi_warehouse_supply_views.xml',
    ],
    'installable': True,
    'application': False,
}