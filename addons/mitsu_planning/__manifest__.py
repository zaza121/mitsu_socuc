# -*- coding: utf-8 -*-
{
    'name': "MITSU PLANNING ADVANCED",
    'version': "18.0.1.0.1",
    'category': 'Planning',
    'summary': """""",
    'description': "",
    'author': "MITSUKI TECHNOLOGIE CONSEIL",
    'company': "MITSUKI TECHNOLOGIE CONSEIL",
    'maintainer': "MITSUKI TECHNOLOGIE CONSEIL",
    'website': "",
    'depends': ['planning', 'sale_planning', 'project_forecast', 'hr_timesheet'],
    'data': [
        # data
        'data/actions_server.xml',
        # views
        'views/planning_slot_views.xml',
        'views/planning_role_views.xml',
        # 'report/account_invoice_report_views.xml',
        # 'report/sale_report_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': "AGPL-3",
    'installable': True,
    'auto_install': False,
    'application': False
}
