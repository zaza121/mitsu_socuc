# -*- coding: utf-8 -*-

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    is_transport_fee = fields.Boolean(string='Frais de transport ?', default=False)
    is_facturation_fee = fields.Boolean(string='Frais de facturation ?', default=False)
    is_degustation = fields.Boolean(string='Degustation ?', default=False)
    facturer_intervention = fields.Boolean(
        string="Facturer Intervention",
        compute="compute_facturer_intervention",
        store=True,
        readonly=False
    )
    order_date_order = fields.Datetime(related="order_id.date_order")

    def write(self, values):
        values = self.check_force_discount(values)
        result = super(SaleOrderLine, self).write(values)
        return result

    def check_force_discount(self, values):
        # because of industry_fsm_sale/models/product_product.py #97 i have to double check the discount value
        if 'discount' in values and values['discount'] < 100:
            if not self.facturer_intervention:
                values['discount'] = 100
        return values
    
    @api.depends("task_id.facturer_intervention")
    def compute_facturer_intervention(self):
        for rec in self:
            if rec.task_id:
                rec.facturer_intervention = rec.task_id.facturer_intervention
            else:
                rec.facturer_intervention = True

    def create_metric_line(self):
        self = self.filtered(lambda x: x.product_id and x.product_id.metrics_ids)
        for rec in self:
            lines = self.env["opsol_costadoro.line_metric"].search([
                ('partner_id', '=', rec.order_id.partner_id.id),('metric_id', 'in', rec.product_id.metrics_ids.ids)])
            for mequip in lines:
                values = {
                    'line_metric_id': mequip.id,
                    'value': rec.product_uom_qty,
                    'note': rec.order_id.name,
                    'date_start': None,
                    'date_end': None,
                }
                self.env["opsol_costadoro.metric_entry"].create(values)

    @api.constrains("facturer_intervention", "is_degustation")
    def force_discount_intervention(self):
        for rec in self:
            discount = 0
            if not rec.facturer_intervention:
                discount = 100
            if rec.is_degustation:
                discount = 100
            rec.discount = discount
    
    @api.constrains("task_id")
    def force_analytic_account(self):
        for rec in self:
            if not rec.analytic_distribution and rec.task_id and rec.task_id.is_fsm:
                account_ana = rec.task_id.analytic_account_id and rec.task_id.analytic_account_id.id or None
                if account_ana:
                    rec.analytic_distribution = {account_ana:100}
