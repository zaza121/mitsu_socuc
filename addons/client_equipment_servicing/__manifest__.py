{
    'name': 'Client Equipment Servicing',
    'version': '1.0',
    'summary': 'Extends Client equipment',
    'author': 'Cyder Solutions',
    'category': 'Productivity',
    'website': 'https://www.cyder.com.au/',
    'price': '99.0',
    'currency': 'USD',
    'sequence': 11,

    'description': """
Extends Client equipment
""",
    'website': 'https://www.cyder.com.au',
    'depends': ['contacts', 'industry_fsm', 'project','sale_management', 'client_equipment','hr'],
    'data': [
        'data/jsa_questions.xml',
        'views/menu.xml',
        'views/contacts_view.xml',
        'views/jobs_view.xml',
        'views/jsa_questions_view.xml',
        'views/project_task_view.xml',
        'views/jsa_pre_responses_view.xml',
        'views/jsa_post_responses_view.xml',
        'report/report.xml',
        'report/jobs_report.xml',



    ],
    'installable': True,
    'application': True,
    'images': ['static/description/banner.gif'],
    'auto_install': False,
    'license': 'OPL-1'
}
