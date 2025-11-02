# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestSaleOrderLineExtension(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})
        self.product = self.env['product.product'].create({'name': 'Test Product', 'type': 'service'})

    def test_apply_force_distribution_from_header(self):
        # Crée un modèle de distribution analytique factice
        model = self.env['account.analytic.distribution.model'].create({
            'name': 'Test Dist',
            'analytic_distribution': {'1': 100}
        })
        sale = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [(0, 0, {'product_id': self.product.id, 'product_uom_qty': 1})],
            'force_distribution_id': model.id,
        })
        line = sale.order_line
        # Après création, la ligne doit avoir la distribution forcée
        self.assertEqual(line.force_modele_id.id, model.id)
        self.assertEqual(line.analytic_distribution, model.analytic_distribution)
