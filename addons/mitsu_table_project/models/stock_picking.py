from odoo import  fields, models, _, api
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)




class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.onchange('transporter_id')
    def _onchange_transporter_id(self):
        for rec in self:
            return {'domain': {'vehicle_id': [('transporter_id', '=', rec.transporter_id.id)]}}

    transporter_id = fields.Many2one("res.partner",
                                  domain=lambda self: [("transporter", "=", True)], string=_('Transporteur'))
    vehicle_id = fields.Many2one("fleet.vehicle", string=_("Camion ou véhicule du transporteur"))
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('transport', _('Transport Confirmé')),
        ('vehicle_in', _("Véhicule à l'entrepôt")),
        ('loading', _("Chargement confirmé")),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ])
    delivery_notes = fields.Char(_("Bordereaux Livraison fournisseur"))
    code_picking_type = fields.Char(_('Code picking'), compute="_compute_picking_type_code",
        store=True)

    def button_validate(self):
        for rec in self:
            if rec.picking_type_id.code == 'outgoing':
                _logger.info('***********************************************')
                _logger.info(rec.state)
                _logger.info(rec.state == 'loading')
                if rec.state != 'loading':
                    raise ValidationError(_("La marchandise doit ètre chargée dans le véhicle"))
                if rec.state == 'loading':
                    pass
        validate = super().button_validate()
        return validate

    def _compute_picking_type_code(self):
        for rec in self:
            rec.code_picking_type = rec.picking_type_id.code


    def confirm_transport(self):
        for rec in self:
            if len(rec.transporter_id) == 0:
                raise ValidationError(_("Choisir le transporteur"))
            rec.state = 'transport'

    def confirm_vehicle(self):
        for rec in self:
            if len(rec.vehicle_id) == 0:
                raise ValidationError(_("Choisir le vehicle"))
            rec.state = 'vehicle_in'

    def confirm_loading(self):
        for rec in self:
            rec.state = 'loading'




