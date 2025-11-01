from odoo.tests import TransactionCase
from odoo.exceptions import ValidationError


class TestPlanningRole(TransactionCase):

    def setUp(self):
        super().setUp()
        self.role = self.env['planning.role'].create({
            'name': 'Test Role',
        })
        self.uom_hour = self.env.ref('uom.product_uom_hour')
        self.uom_day = self.env.ref('uom.product_uom_day')

    def test_create_cost_line(self):
        """Test: Création d'une ligne de coût."""
        cost = self.env['mitsu_sale.cost_role_line'].create({
            'role_id': self.role.id,
            'uom_id': self.uom_hour.id,
            'amount': 50.0,
        })

        self.assertEqual(cost.amount, 50.0)
        self.assertEqual(len(self.role.cost_ids), 1)

    def test_duplicate_uom_constraint(self):
        """Test: Contrainte d'unicité UOM par rôle."""
        self.env['mitsu_sale.cost_role_line'].create({
            'role_id': self.role.id,
            'uom_id': self.uom_hour.id,
            'amount': 50.0,
        })

        with self.assertRaises(ValidationError):
            self.env['mitsu_sale.cost_role_line'].create({
                'role_id': self.role.id,
                'uom_id': self.uom_hour.id,
                'amount': 60.0,
            })

    def test_negative_amount_constraint(self):
        """Test: Montant négatif interdit."""
        with self.assertRaises(ValidationError):
            self.env['mitsu_sale.cost_role_line'].create({
                'role_id': self.role.id,
                'uom_id': self.uom_hour.id,
                'amount': -50.0,
            })
