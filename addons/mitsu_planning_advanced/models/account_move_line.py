from odoo import api, fields, models

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    margin_amount = fields.Float(string='Margin Amount', compute='_compute_margin', store=True)
    margin_percentage = fields.Float(string='Margin Percentage', compute='_compute_margin', store=True)

    @api.depends('quantity', 'price_unit', 'discount', 'product_id.standard_price')
    def _compute_margin(self):
        for line in self:
            std_price = line.product_id.standard_price or 0.0
            sale_total = line.price_unit * line.quantity * (1 - line.discount / 100)
            cost_total = std_price * line.quantity
            margin = sale_total - cost_total
            line.margin_amount = margin
            line.margin_percentage = (margin / sale_total * 100) if sale_total else 0