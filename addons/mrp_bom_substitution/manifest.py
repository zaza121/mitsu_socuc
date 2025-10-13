{
    "name": "MRP BOM Substitution",
    "version": "1.0",
    "summary": "Substitute BOM components on shortage and trigger purchase orders.",
    "author": "Your Name",
    "website": "Your Website",
    "license": "LGPL-3",
    "depends": ["mrp", "stock", "purchase"],
    "data": [
        "views/mrp_bom_views.xml",
        "views/mrp_production_views.xml",
        "data/ir_cron.xml"
    ],
    "installable": True,
    "application": False,
    "auto_install": False
}