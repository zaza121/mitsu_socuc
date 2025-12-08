# -*- coding: utf-8 -*-
{
    "name": "Sale Order Line - Planning Role & Analytic Distribution",
    "version": "1.0.0",
    "category": "Sales",
    "summary": "Intègre les rôles de planification et les modèles analytiques sur les lignes de vente (Odoo 18)",
    "author": "MITSUKI TECHNOLOGIE CONSEIL",
    "license": "LGPL-3",
    "depends": [
        "sale_management",
        "account",
        "project",
        "planning",
        "mitsu_sale"
    ],
    "data": [
        "security/ir.model.access.csv",
        # "views/sale_order_line_views.xml",
    ],
    "tests": [
        "tests/test_sale_order_line.py",
    ],
    "installable": True,
    "application": False,
}
