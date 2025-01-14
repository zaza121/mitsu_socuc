from odoo import fields, models, _


class DeliveryCarrierPurchase(models.Model):
    _inherit = 'delivery.carrier'

    city_delivery = fields.Many2one('res.city', string=_("Dépôt de destination"))
    delivery_bag_value = fields.Monetary(string=_("TRANSP/SACS"))