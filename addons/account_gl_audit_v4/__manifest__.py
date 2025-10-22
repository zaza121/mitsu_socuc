# -*- coding: utf-8 -*-

{
    "name": "Audit Grand Livre SYSCOHADA (Optimisé)",
    "version": "1.0.3",
    "category": "Accounting",
    "summary": "Audit Grand Livre SYSCOHADA avec périodes, classes de comptes et export Excel (Odoo 18 optimisé)",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",  <-- NOUVELLE LIGNE AJOUTÉE
        "views/audit_grand_livre_views.xml",
    ],
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}