from odoo.tests.common import TransactionCase

class TestSaleProjectTaskLink(TransactionCase):

    def setUp(self):
        super().setUp()
        Project = self.env['project.project']
        Task = self.env['project.task']
        ProductTmpl = self.env['product.template']
        SaleOrder = self.env['sale.order']
        SaleLine = self.env['sale.order.line']

        # Créer projet template
        self.proj_template = Project.create({'name': 'Template Project Test'})
        # Tâche template
        self.task_template = Task.create({
            'name': 'Task Template A',
            'project_id': self.proj_template.id,
        })
        # Produit lié
        tmpl = ProductTmpl.create({
            'name': 'Produit Test',
            'type": "product",
            'task_template_id': self.task_template.id,
        })
        self.product = tmpl.product_variant_id
        # Analytic + commande
        analytic = self.env['account.analytic.account'].create({'name': 'Analytic Test'})
        self.sale = SaleOrder.create({
            'partner_id': self.env.ref('base.res_partner_1').id,
            'analytic_account_id': analytic.id,
        })
        self.line = SaleLine.create({
            'order_id': self.sale.id,
            'product_id': self.product.id,
            'product_uom_qty': 1,
            'price_unit': 10,
        })
        # Projet lié à analytic
        self.project = Project.create({
            'name': 'Project for Sale',
            'analytic_account_id': analytic.id,
        })

    def test_task_created_and_linked(self):
        self.sale.action_confirm()
        task = self.env['project.task'].search([
            ('project_id', '=', self.project.id),
            ('template_task_id', '=', self.task_template.id),
        ], limit=1)
        self.assertTrue(task, "Tâche non créée")
        self.assertEqual(task.sale_line_id, self.line)
        self.assertEqual(task.product_id, self.product)
