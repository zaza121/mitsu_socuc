{
"name": "Account Financial Report Analytic Breakdown",
"version": "1.2.0",
"summary": "Add analytic-plan columns and totals to financial reports (balance / P&L) with UI selector, memory per user and Excel export (Odoo 18)",
"description": "Adds analytic breakdown with plan selector in financial reports, user preference memory, total column option, and XLSX export.",
"author": "Auto Generated",
"license": "OEEL-1",
"category": "Accounting/Localisation",
"depends": ["account","web","base"],
"data": [
"views/res_config_settings_views.xml",
"views/account_reports_templates.xml",
"views/assets.xml",
"security/ir.model.access.csv"
],
"assets": {
"web.assets_backend": [
"account_financial_analytic_breakdown/static/src/js/report_analytic_selector.js",
"account_financial_analytic_breakdown/static/src/xml/report_analytic_selector.xml"
]
},
"installable": true,
"application": false,
"auto_install": false
}