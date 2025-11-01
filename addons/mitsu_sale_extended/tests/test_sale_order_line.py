from odoo.tests import TransactionCase


class TestSaleOrderLine(TransactionCase):

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test Customer',
        })
        # Create a product template and product with service type and hourly UoM
        uom_hour = self.env.ref('uom.product_uom_hour')
        template = self.env['product.template'].create({
            'name': 'Test Service Template',
            'type': 'service',
            'uom_id': uom_hour.id,
        })
        self.product = self.env['product.product'].search([('product_tmpl_id', '=', template.id)], limit=1)
        if not self.product:
            # fallback: create product.product directly
            self.product = self.env['product.product'].create({
                'name': 'Test Service',
                'type': 'service',
                'uom_id': uom_hour.id,
            })

        self.role = self.env['planning.role'].create({
            'name': 'Consultant',
        })
        self.uom_hour = uom_hour
        self.cost_line = self.env['mitsu_sale.cost_role_line'].create({
            'role_id': self.role.id,
            'uom_id': self.uom_hour.id,
            'amount': 100.0,
        })
        self.order = self.env['sale.order'].create({'partner_id': self.partner.id})
        self.line = self.env['sale.order.line'].create({
            'order_id': self.order.id,
            'product_id': self.product.id,
            'product_uom': self.uom_hour.id,
            'product_uom_qty': 1.0,
            'role_id': self.role.id,
        })

    def test_role_cost_applied(self):
        """Test: Le rôle met à jour le prix unitaire."""
        # Simuler l'onchange qui est normalement déclenché par l'UI
        self.line._onchange_role_id()
        self.assertEqual(self.line.price_unit, 100.0)
