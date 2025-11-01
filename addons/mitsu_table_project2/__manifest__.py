# -*- coding:utf-8 -*-
{
    'name': 'Mitsu Table Project',
    'version': '1.0.0',
    'category': 'Project',
    'summary': 'Tableau & rapport planning projet (calculs coûts, marges, CA)',
    'author': 'MITSU',
    'license': 'AGPL-3',
    'sequence': 30,
    'depends': ['mitsu_planning', 'mitsu_hr', 'planning', 'project', 'sale_timesheet', 'account', 'delivery', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'views/planning_slot_view.xml',
        'views/reportpla_views.xml',
        'data/delivery_and_product_services.xml',
        'data/report_data.xml',
        'data/res_city_data.xml',
    ],
    'application': False,
}