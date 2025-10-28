# -*- coding: utf-8 -*-
{
    'name': "Audit Grand Livre PCG Français (Optimisé)",
    'version': '16.0.1.0.0',
    'summary': """Détecte les anomalies de solde dans le Grand Livre selon le Plan Comptable Général (PCG) français.""",
    'description': """
        Ce module Transient permet d'auditer rapidement de grands volumes d'écritures
        pour identifier les anomalies de solde (débiteur/créditeur) selon les règles
        des classes de comptes du PCG (Classes 1 à 7).
    """,
    'author': "Votre Nom",
    'website': "http://www.votre-site.com",
    'category': 'Accounting/Audit',
    'depends': ['account', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'views/audit_grand_livre_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}