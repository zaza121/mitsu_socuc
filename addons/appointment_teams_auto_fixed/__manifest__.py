{
    'name': 'Appointment Teams Auto [FIXED]',
    'version': '1.0',
    'summary': 'Génération automatique de réunions Microsoft Teams pour les rendez-vous après paiement.',
    'description': """
Intégration Microsoft Teams pour les rendez-vous Odoo 18, déclenchée par le paiement de la facture.
- Gestion des credentials via les paramètres.
- Cache du token OAuth2 (client credentials).
- Création d'onlineMeeting et insertion du lien dans l'événement de calendrier.
""",
    'category': 'Services/Appointment',
    'author': 'TonNom / TonEntreprise (Fixes Applied)',
    'depends': ['calendar_appointment', 'website_calendar', 'base', 'account', 'sale_management'],
    'data': [
        'security/ir.model.access.csv', 
        'views/appointment_views.xml',
        'views/settings_views.xml',
        'data/mail_template_inherit.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
