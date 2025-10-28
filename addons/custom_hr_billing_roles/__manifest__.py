{
'name': "HR Billing Roles Customization",
'version': '18.0.1.0.0',
'depends': ['sale_management', 'hr', 'product'],
'data': [
'security/ir.model.access.csv',
'views/role_pricing_views.xml',
'views/sale_order_views.xml',
],
'installable': True,
'application': False,
'license': 'LGPL-3',
}