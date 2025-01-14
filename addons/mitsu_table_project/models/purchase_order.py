from odoo import api, fields, models, _
import logging

from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)
EXPEDITION = [
    ('self_collection', 'SELF COLLECTION'),
    ('dantrans', 'DANTRANS'),
]

class PurchasOrder(models.Model):
    _inherit = "purchase.order"

    city_delivery = fields.Many2one('res.city', string=_("Dépôt de destination"))
    contact_delivery = fields.Many2one('res.partner', string=_("Contact Destinataire"))
    delivery_bag_value= fields.Monetary(string=_("TRANSP/SACS"))
    is_paid_delivery = fields.Boolean(string=_('A frais transport fournissaur'),
      compute="_compute_is_paid_delivery", store=True)

    expedition_mode = fields.Selection(EXPEDITION, _("Mode Expedition"), default='self_collection')

    @api.depends('order_line')
    def _compute_is_paid_delivery(self):
        for rec in self:
            for line in  rec.order_line:
                if (line.product_id.categ_id.name == 'Deliveries') and (
                        line.product_id.type == 'service'):
                    return True
        return False

    def product_have_delivery(self):
        for rec in self:
            for line in rec.order_line:
                if (line.product_id.categ_id.name == 'Deliveries') and (
                        line.product_id.type == 'service'):
                    return len(rec.city_delivery) == 0 or rec.delivery_bag_value == 0 \
                or rec.expedition_mode == 'self_collection'
        return False

    def button_confirm(self):
        for rec in self:
            _logger.info("*****************************************************")
            _logger.info((self.product_have_delivery()))
            _logger.info("*****************************************************")
            if self.product_have_delivery():
                raise ValidationError("Veuillez définir le dépôt de destination, "
                        "le mode d'expédition et le prix par sac.")
        result = super(PurchasOrder, self).button_confirm()
        return result



