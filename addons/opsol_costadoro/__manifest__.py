# -*- coding: utf-8 -*-
{
    'name': "Odoo for Costadoro by Opensolution",

    'summary': """.""",

    'description': """
       Customisation for Costadoro by Opensolution
    """,
    "license": "LGPL-3",
    'author': "OpenSolution",
    'website': "http://www.opensolution.mc",

    'category': 'Sale',
    'version': '1.18.0',

    'depends': [
        'sale', 'account', 'client_equipment_servicing', 'tracking_manager', 'base_automation',
        'industry_fsm_sale', 'stock',
    ],

    'data': [
        # cron
        'data/cron.xml',
        # views
        'views/menus.xml',
        'views/sale_order_views.xml',
        'views/sale_order_line_views.xml',
        'views/metric_entry_views.xml',
        'views/project_task_views.xml',
        'views/equipment_details_views.xml',
        'views/metrique_equip_views.xml',
        'views/line_metric_views.xml',
        'views/zone_comm_views.xml',
        'views/res_partner_views.xml',
        'views/equip_move_history_views.xml',
        'views/fsm_views.xml',
        'views/product_template_views.xml',
        'views/model_equip_views.xml',
        'views/project_task_type_views.xml',
        'views/equipment_jobs_views.xml',
        'views/equipment_category_views.xml',
        'views/jour_semaine_views.xml',
        # security
        'security/ir.model.access.csv',
        # wizards
        # 'wizards/hyd_import_so_line_view.xml',
        # 'wizards/clear_so_wizard.xml',
        'wizards/eq_addentry_wiz_views.xml',
        # repotrts
        "reports/stock_comparartif_report.xml",
    ],
    'assets': {
        'web.assets_backend': [],
        'web.assets_frontend': [],
    },

    'demo': [],
}
