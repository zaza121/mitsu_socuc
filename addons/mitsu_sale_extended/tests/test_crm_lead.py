from odoo.tests import TransactionCase


class TestCrmLead(TransactionCase):

    def setUp(self):
        super().setUp()
        self.distribution = self.env['account.analytic.distribution.model'].create({
            'name': 'Test Distribution',
        })

    def test_quotation_context_with_distribution(self):
        """Test: Le contexte inclut le modèle de distribution."""
        lead = self.env['crm.lead'].create({
            'name': 'Test Lead',
            'distribution_id': self.distribution.id,
        })

        ctx = lead._prepare_opportunity_quotation_context()

        self.assertIn('default_force_distribution_id', ctx)
        self.assertEqual(ctx['default_force_distribution_id'], self.distribution.id)
