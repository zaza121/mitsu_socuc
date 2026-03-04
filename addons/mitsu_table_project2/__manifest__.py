# -*- coding: utf-8 -*-
{
    "name": "Mitsu – Rentabilité Projet",
    "version": "18.0.1.0.0",
    "category": "Project",
    "summary": "Analyse de rentabilité projet (Prévisionnel / Réel)",
    "description": """
Analyse avancée de rentabilité projet :
- Heures vendues vs réalisées
- CA / Coût / Marge
- Analyse par période (mois / année)
- Analyse par compte analytique
- Vue liste & pivot
""",
    "author": "Mitsu",
    "license": "LGPL-3",
    "depends": [
        "project",
        "sale_project",
        "hr_timesheet",
        "planning",
        "account"
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        # 1. Charger la recherche en premier pour que l'action puisse la trouver
        "views/mitsu_task_allocation_search.xml", 
        # 2. Charger les définitions de vues (Liste/Pivot)
        "views/mitsu_task_allocation_views.xml",
        "views/mitsu_task_allocation_pivot.xml",
        # 3. Charger l'action et le menu en dernier
        "views/mitsu_task_allocation_action.xml",
    ],
    "installable": True,
    "application": False,
}