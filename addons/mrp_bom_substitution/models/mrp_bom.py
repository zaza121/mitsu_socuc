from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    bom_line_ids = fields.One2many(
        'mrp.bom.line', 'bom_id', 'BoM Lines',
        copy=True, auto_join=True)

class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    alternative_component_ids = fields.Many2many(
        'product.product', string='Alternative Components',
        domain="[('type', '=', 'product'), ('sale_ok', '=', True)]",
        help="Alternative components to use when the original component is out of stock.")
    priority = fields.Integer(string='Priority', default=10,
        help="Priority of the alternative component. Lower number means higher priority.")

    @api.constrains('alternative_component_ids')
    def _check_alternative_components(self):
        for line in self:
            if line.product_id in line.alternative_component_ids:
                raise ValidationError(_("A component cannot be an alternative to itself."))
