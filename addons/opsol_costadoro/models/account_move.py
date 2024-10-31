
from odoo import api, fields, models, Command, _
import logging
import functools

LABEL_RUBRIQUE = {
    'mepa': 'ME Parts','meot': 'ME Others',
    'gspa': 'GS Parts', 'gsot': 'GS Others',
    'gbpa': 'GB Parts', 'gbot': 'GB Others',
    'gsadpa': 'Supply Parts', 'gsadot': 'GS AD Others'}


class AccountMove(models.Model):
    _inherit = 'account.move'

    auto_order_line = fields.Boolean(
        string='Auto group line by rubrique',
        default=True
    )
    opsol_sale_order_ids = fields.Many2many(
        comodel_name='sale.order',
        compute="_compute_sale_order_ids",
        string='Sale orders',
        store=True
    )
    opsol_sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        compute="_compute_sale_order_ids",
        string='Sale Order',
        store=True
    )

    @api.depends("line_ids")
    def _compute_sale_order_ids(self):
        for rec in self:
            sal_ords = rec.line_ids.sale_line_ids.order_id
            rec.opsol_sale_order_ids = sal_ords
            rec.opsol_sale_order_id = sal_ords and sal_ords[0] or False

    def write(self, values):
        res = super(AccountMove, self).write(values)
        if values.get('invoice_line_ids'):
            self.reorder_line()
        return res

    def reorder_line(self):

        if self._context.get('no_call_reorder', False):
            return True

        if not self.auto_order_line:
            return []

        new_sequences = []

        moves_lines = self.invoice_line_ids
        # delete all section & notes
        sections_notes = moves_lines.filtered(lambda x: x.display_type in ["line_section", "line_note"])
        new_sequences += [Command.delete(elt.id) for elt in sections_notes]
        moves_lines -= sections_notes

        self.env["account.move.line"].flush_model()

        # get rubriques
        rubriques = LABEL_RUBRIQUE.keys()

        # compute formatter
        round_digit = 2
        decimal_precision = self.env.ref("product.decimal_price")
        if decimal_precision:
            round_digit = decimal_precision.digits

        # reset sequence
        seq = 10
        new_sequences += [Command.delete(elt.id) for elt in sections_notes]

        for rubrique in rubriques:
            lines_rub = moves_lines.filtered(lambda x: x.rubrique == rubrique).sorted(
                key=lambda r: r.product_id.name)

            if not lines_rub:
                continue

            moves_lines -= lines_rub

            total = sum(lines_rub.mapped("price_total"))
            total = round(total, round_digit)

            # add new section by rubrique
            new_sequences.append(Command.create({
                "sequence": seq, "display_type": "line_section",
                "name": LABEL_RUBRIQUE.get(rubrique, ""),
            }))
            seq = seq + 1

            for line in lines_rub:
                new_sequences.append(Command.update(line.id, {"sequence": seq}))
                seq = seq + 1

            # add total for rubrique
            name = _("Total {}: {:,.2f} {}").format(
                LABEL_RUBRIQUE.get(rubrique, ""), total, self.currency_id.symbol)

            new_sequences.append(Command.create({
                "sequence": seq, "display_type": "line_note",
                "name": name
            }))
            seq = seq + 1

        self.with_context(no_call_reorder=True).write({"invoice_line_ids": new_sequences})
    
    @api.constrains('state')
    def force_reorder_oncreate(self):
        for rec in self:
            if rec.state == 'draft':
                rec.reorder_line()
