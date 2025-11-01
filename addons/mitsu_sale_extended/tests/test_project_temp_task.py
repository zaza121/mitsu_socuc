from odoo.tests import TransactionCase


class TestProjectTempTask(TransactionCase):

    def setUp(self):
        super().setUp()
        self.project = self.env['project.project'].create({
            'name': 'Test Project',
        })

    def test_create_temp_task(self):
        tmpl = self.env['mitsu_sale.project_temp_task'].create({
            'name': 'Task A',
            'project_temp_id': self.project.id,
            'planned_hours': 2.0,
        })
        self.assertEqual(tmpl.name, 'Task A')
        self.assertEqual(tmpl.planned_hours, 2.0)
