
from odoo import api, fields, models, Command, _
import logging
import functools


class RemanLine(models.Model):
    _name = "opsol_ajmarine.reman_line"

    order_id = fields.Many2one(
        comodel_name='sale.order',
        string='Order',
    )
    line_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='SO Line',
        ondelete="cascade",
        check_company=True,
    )
    product_id = fields.Many2one(
        comodel_name='product.product',
        related="line_id.product_id",
    )
    name = fields.Text(related="line_id.name")
    qty = fields.Float(related="line_id.product_uom_qty")
    so_reference = fields.Char(related="line_id.so_reference")
    amount_caution = fields.Monetary(string="Caution")
    total_caution = fields.Monetary(
        string="Total caution",
        compute="compute_total_caution",
        stored=True
    )
    currency_id = fields.Many2one(related="line_id.currency_id")
    company_id = fields.Many2one(related="line_id.company_id")

    @api.depends('qty', 'amount_caution')
    def compute_total_caution(self):
        for rec in self:
            rec.total_caution = rec.qty * rec.amount_caution

    @api.ondelete(at_uninstall=False)
    def on_delete_record(self):
        for rec in self:
            rec.line_id.unlink()
