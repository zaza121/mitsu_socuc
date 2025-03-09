# -*- coding:utf-8 -*-
# Author: MITSU
{
    'name': 'Mutsi Planning',
    'version': '1.0',
    'category': 'Porject',
    'author': 'MITSU',
    'sequence' : -100,
    'depends': ['mitsu_planning', 'mitsu_hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/planning_slot_view.xml',
        'views/reportpla_views.xml',
       
    ],
    'application' : True,
}