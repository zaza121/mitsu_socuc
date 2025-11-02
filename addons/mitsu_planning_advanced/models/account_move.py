from odoo import api, fields, models

class AccountMove(models.Model):
    _inherit = 'account.move'

    margin_amount = fields.Float(string='Total Margin', compute='_compute_margin', store=True)
    margin_percentage = fields.Float(string='Margin %', compute='_compute_margin', store=True)

    @api.depends('invoice_line_ids.margin_amount', 'invoice_line_ids.price_subtotal')
    def _compute_margin(self):
        for move in self:
            total_sales = sum(move.invoice_line_ids.mapped('price_subtotal'))
            total_margin = sum(move.invoice_line_ids.mapped('margin_amount'))
            move.margin_amount = total_margin
            move.margin_percentage = (total_margin / total_sales * 100) if total_sales else 0