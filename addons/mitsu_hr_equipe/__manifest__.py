{
  'name': 'HR Employee Team',
  'version': '18.0.1.0.0',
  'category': 'Human Resources',
  'summary': 'Gestion des équipes de travail avec planning',
  'description': "Permet de créer des équipes, gérer les membres et filtrer le planning par équipe.",
  'author': 'Votre Entreprise',
  'website': 'https://www.votresite.com',
  'depends': ['hr', 'planning'],
  'data': [
    'security/ir.model.access.csv',
    'views/hr_team_views.xml',
    'views/planning_views.xml'
  ],
  'license': 'LGPL-3',
  'installable': True,
  'application': False
}