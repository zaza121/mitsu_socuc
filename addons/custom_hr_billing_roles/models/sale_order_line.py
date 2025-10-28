from odoo import models, fields, api

class SaleOrderLine(models.Model):
_inherit = 'sale.order.line'

role_id = fields.Many2one('hr.job', string="Rôle")

@api.onchange('role_id', 'product_uom')
def _onchange_role_pricing(self):
if self.role_id and self.product_uom:
pricing = self.env['role.pricing'].search([
('role_id', '=', self.role_id.id),
('uom_id', '=', self.product_uom.id),
('company_id', '=', self.company_id.id if self.company_id else self.env.company.id)
], limit=1)
if pricing:
self.price_unit = pricing.price