from odoo import fields, models, _
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = "sale.order"


    def create_line_cost_delivery(self, order_line, purchase_order):
        purchase_line_vals = {
            'name': order_line.product_template_id.name,
            'product_qty': 1,
            'product_id': order_line.product_template_id.id,
            'product_uom': order_line.product_template_id.uom_po_id.id,
            'price_unit': order_line.price_unit,
            'taxes_id': [(6, 0, order_line.tax_id.ids)],
            'order_id': purchase_order.id,
            'sale_line_id': order_line.id,

        }
        if order_line.analytic_distribution:
            purchase_line_vals['analytic_distribution'] = order_line.analytic_distribution
        return purchase_line_vals

    def add_line_cost_delivery_purchase_order(self,purchase_order_value):
        purchase_line = self.env['purchase.order.line'].create(purchase_order_value)
        return True

    def add_city_delivery_bag_purchase_order(self):
        pass

    def validation_number_bag(self, order_line):
        """ Function that checks if the number of cement bags equals 640 in the case of the shipment"""
        for line in order_line:
            if (line.product_template_id.categ_id.name == 'All') and (
                    line.product_template_id.type == 'consu'):
                return line.product_uom_qty != 640
        return True


    def _action_confirm(self):
        result = super(SaleOrder, self)._action_confirm()
        for rec in self:
            purchase = rec.order_line.purchase_line_ids[0].order_id
            for data in rec.order_line:
                if (data.product_template_id.categ_id.name == 'Deliveries') and (data.product_template_id.type == 'service'):
                    if rec.validation_number_bag(rec.order_line):
                        raise ValidationError("Le nombre de sacs doit correspondre à 640.")
                    purchase_value = self.create_line_cost_delivery(data,purchase)
                    purchase_line_add = self.add_line_cost_delivery_purchase_order(purchase_value)
        #raise ValidationError("Test get purchasse")
        return result

