from odoo import fields, models, _


class FleetVehicleLoading(models.Model):
    _inherit = 'fleet.vehicle'

    transporter_id = fields.Many2one("res.partner",
        domain=lambda self: [("transporter","=",True)],string=_('Transporteur'))




