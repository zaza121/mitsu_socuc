# -*- coding: utf-8 -*-
from odoo import api, fields, models, Command, _
from odoo.osv import expression
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    role_id = fields.Many2one(
        comodel_name='planning.role',
        string='Role',
    )
    force_modele_id = fields.Many2one(
        comodel_name='account.analytic.distribution.model',
        string='Force Modele analytique',
    )

    @api.onchange('role_id', 'product_uom', 'product_uom_qty')
    def _onchange_role_id(self):
        if self.role_id and self.product_uom:
            line = self.role_id.cost_ids.filtered(lambda x: x.uom_id.id == self.product_uom.id)
            if line:
                self.price_unit = line.amount

    @api.onchange('force_modele_id')
    def _onchange_force_modele_id(self):
        anadist = {}

        if self.force_modele_id:
            anadist.update(self.force_modele_id.analytic_distribution)
        self.analytic_distribution = anadist

    @api.depends('order_id.partner_id', 'product_id')
    def _compute_analytic_distribution(self):
        with_distri = self.filtered(lambda x: x.order_id.force_distribution_id)
        without_distri = self - with_distri
        for line in with_distri:
            line.force_modele_id = line.order_id.force_distribution_id
            line.analytic_distribution = line.order_id.force_distribution_id.analytic_distribution
        super(SaleOrderLine, with_distri)._compute_analytic_distribution()

    def _timesheet_create_project_prepare_values(self):
        res = super()._timesheet_create_project_prepare_values()

        if self.analytic_distribution:
            keys = ','.join(self.analytic_distribution.keys())
            ana_dist = [int(elt) for elt in keys.split(",")]
            accounts = self.env["account.analytic.account"].browse(ana_dist)
            map_plan_acc = {acc.plan_id.id: acc.id for acc in accounts}
            map_fields_plan = {f"x_plan{p.id}_id": map_plan_acc.get(p.id) for p in accounts.mapped("plan_id")}
            fields = self.env["ir.model.fields"].search([
                ('model_id.model', '=', "project.project"),
                ('name', 'in', list(map_fields_plan.keys()))
            ])

            for _fie in fields:
                res[_fie.name] = map_fields_plan.get(_fie.name, None)
        return res

    def _timesheet_service_generation(self):
        res = super()._timesheet_service_generation()

        for rec in self:

            task_obj = self.env["project.task"]
            if rec.product_id.service_tracking == 'project_only':
                name_task = rec.product_id.mapped("temp_task_ids.name")
                for _name in name_task:
                    values = {
                        'name': _name,
                        # 'allocated_hours': rec._convert_qty_company_hours(rec.company_id),
                        'partner_id': rec.order_id.partner_id.id,
                        'description': '<br/>'.join(rec.name.split('\n')),
                        'project_id': rec.project_id.id,
                        'sale_line_id': rec.id,
                        'sale_order_id': rec.order_id.id,
                        'company_id': rec.company_id.id,
                        'user_ids': False,  # force non assigned task, as created as sudo()
                    }
                    # raise Warning(values)
                    task_obj.create(values)

    @api.constrains("order_id.project_id", 'state')
    def get_project_account_id(self):
        for rec in self:
            if rec.project_id and rec.project_id.account_id:
                account = rec.project_id.account_id
                ana_lines =  rec.analytic_distribution and rec.analytic_distribution.keys() or []
                found_in = [k for k in ana_lines if f"{account.id}" in k]
                if not found_in:
                    gop = rec.analytic_distribution or {}
                    gop.update({f"{account.id}": 100})
                    rec.analytic_distribution = gop
