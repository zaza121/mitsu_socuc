from odoo import models, fields, api, _, tools
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _action_confirm(self):
        res = super()._action_confirm()
        for production in self:
            production._check_bom_availability_and_procure()
        return res

    def _check_bom_availability_and_procure(self):
        PurchaseOrder = self.env['purchase.order']
        PurchaseOrderLine = self.env['purchase.order.line']

        for move in self.move_raw_ids:
            product = move.product_id
            qty_required = move.product_uom_qty

            if float_compare(product.qty_available, qty_required, precision_rounding=product.uom_id.rounding) < 0:
                bom_line = move.bom_line_id
                product_name = product.display_name

                substituted = False
                if bom_line and bom_line.alternative_component_ids:
                    alternatives = bom_line.alternative_component_ids.sorted(key=lambda p: p.priority)
                    for alt in alternatives:
                        if float_compare(alt.qty_available, qty_required, precision_rounding=alt.uom_id.rounding) >= 0:
                            move.write({
                                'product_id': alt.id,
                                'name': alt.name,
                            })
                            self.message_post(body=_(
                                "🔄 Composant '%s' remplacé par l'alternative '%s' (priorité %s) — stock suffisant détecté."
                            ) % (product_name, alt.name, alt.priority))
                            substituted = True
                            break

                if not substituted:
                    self.message_post(body=_(
                        "❌ Aucune alternative avec un stock suffisant n’a été trouvée pour '%s'."
                    ) % product_name)

                seller = product._select_seller()
                if not seller:
                    raise UserError(_("Aucun fournisseur trouvé pour le produit %s.") % product_name)

                orderpoint = self.env['stock.warehouse.orderpoint'].search([
                    ('product_id', '=', product.id)
                ], limit=1)

                if orderpoint:
                    qty_to_order = orderpoint.product_min_qty or qty_required
                else:
                    qty_to_order = qty_required

                purchase_order = PurchaseOrder.search([
                    ('partner_id', '=', seller.name.id),
                    ('state', '=', 'draft'),
                ], limit=1)

                if not purchase_order:
                    purchase_order = PurchaseOrder.create({
                        'partner_id': seller.name.id,
                        'date_order': fields.Date.today(),
                    })

                po_line = purchase_order.order_line.filtered(lambda l: l.product_id == product)
                if po_line:
                    po_line.product_qty += qty_to_order
                else:
                    PurchaseOrderLine.create({
                        'order_id': purchase_order.id,
                        'product_id': product.id,
                        'name': product.name,
                        'product_qty': qty_to_order,
                        'product_uom': product.uom_po_id.id,
                        'price_unit': seller.price,
                        'date_planned': fields.Datetime.now(),
                    })

                self.message_post(body=_(
                    "🛒 Commande d'achat générée pour '%s' — quantité : %s (via réapprovisionnement)."
                ) % (product_name, qty_to_order))
