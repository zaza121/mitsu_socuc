# -*- coding: utf-8 -*-
{
    'name': "MITSU Sale extended",
    'version': "18.0.1.0.1",
    'category': 'Sales',
    'summary': """""",
    'description': "",
    'author': "MITSUKI TECHNOLOGIE CONSEIL",
    'company': "MITSUKI TECHNOLOGIE CONSEIL",
    'maintainer': "MITSUKI TECHNOLOGIE CONSEIL",
    'website': "",
    'depends': ['sale', 'crm', 'sale_crm', 'planning', 'sale_project'],
    'data': [
        # views
        'views/crm_lead_views.xml',
        'views/sale_order_views.xml',
        'views/planning_role_views.xml',
        'views/analytic_distribution_model_views.xml',
        'views/project_project_views.xml',
        'views/project_temp_task_views.xml',
        'views/product_template_views.xml',
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
