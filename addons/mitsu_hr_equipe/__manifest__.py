# -*- coding: utf-8 -*-
{
   'name': "MITSU HR extended",
   'version': "18.0.1.0.1",
   'category': 'Human Resources',
   'summary': "Extensions RH : équipes, intégration planning et produits",
   'description': "Ajoute la notion d\'équipes, propagation des managers vers le planning et "
                  "liaison produit -> ressource (prix = coût horaire).",
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
       # security
       'security/ir.model.access.csv',
   ],
   'images': ['static/description/banner.jpg'],
   'license': "AGPL-3",
   'installable': True,
   'auto_install': False,
   'application': False,
}
