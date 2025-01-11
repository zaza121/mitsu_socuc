# -*- coding: utf-8 -*-
{
    'name': "MITSU HR extended",
    'version': "18.0.1.0.1",
    'category': 'Human Resources',
    'summary': """""",
    'description': "",
    'author': "MITSUKI TECHNOLOGIE CONSEIL",
    'company': "MITSUKI TECHNOLOGIE CONSEIL",
    'maintainer': "MITSUKI TECHNOLOGIE CONSEIL",
    'website': "",
    'depends': ['hr', 'planning', 'timesheet_grid', 'sale_planning'],
    'data': [
        # views
        'views/equipe_views.xml',
        'views/hr_employee_views.xml',
        'views/planning_slot_views.xml',
        'views/product_template_views.xml',
        'views/hr_department_views.xml',
        #security
        'security/ir.model.access.csv',
        # 'report/account_invoice_report_views.xml',
        # 'report/sale_report_views.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'license': "AGPL-3",
    'installable': True,
    'auto_install': False,
    'application': False
}