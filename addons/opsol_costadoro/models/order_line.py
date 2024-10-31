
from odoo import api, fields, models, Command, _
import logging
import functools


class InhOrderLine(models.AbstractModel):
    _inherits = {'sale.order.line': 'line_id'}
    _name = "opsol_ajmarine.inh_order_line"

    line_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='SO Line',
        ondelete="cascade",
        check_company=True,
    )

    @api.ondelete(at_uninstall=False)
    def on_delete_record(self):
        for rec in self:
            rec.line_id.unlink()


class MEPAOrderLine(models.Model):
    _inherit = "opsol_ajmarine.inh_order_line"
    _name = "opsol_ajmarine.mepa_order_line"
    _description = "Order Line for ME Parts"

    def action_add_from_catalog(self):
        order = self.env['sale.order'].browse(self.env.context.get('order_id'))
        return order.with_context(aj_rub='mepa').action_add_from_catalog()


class MEOTOrderLine(models.Model):
    _inherit = "opsol_ajmarine.inh_order_line"
    _name = "opsol_ajmarine.meot_order_line"
    _description = "Order Line for ME Others"

    def action_add_from_catalog(self):
        order = self.env['sale.order'].browse(self.env.context.get('order_id'))
        return order.with_context(aj_rub='meot').action_add_from_catalog()


class GSPAOrderLine(models.Model):
    _inherit = "opsol_ajmarine.inh_order_line"
    _name = "opsol_ajmarine.gspa_order_line"
    _description = "Order Line for GS Parts"

    def action_add_from_catalog(self):
        order = self.env['sale.order'].browse(self.env.context.get('order_id'))
        return order.with_context(aj_rub='gspa').action_add_from_catalog()


class GSOTOrderLine(models.Model):
    _inherit = "opsol_ajmarine.inh_order_line"
    _name = "opsol_ajmarine.gsot_order_line"
    _description = "Order Line for GS Others"

    def action_add_from_catalog(self):
        order = self.env['sale.order'].browse(self.env.context.get('order_id'))
        return order.with_context(aj_rub='gsot').action_add_from_catalog()

class GBPAOrderLine(models.Model):
    _inherit = "opsol_ajmarine.inh_order_line"
    _name = "opsol_ajmarine.gbpa_order_line"
    _description = "Order Line for GB Parts"

    def action_add_from_catalog(self):
        order = self.env['sale.order'].browse(self.env.context.get('order_id'))
        return order.with_context(aj_rub='gbpa').action_add_from_catalog()

class GBOTOrderLine(models.Model):
    _inherit = "opsol_ajmarine.inh_order_line"
    _name = "opsol_ajmarine.gbot_order_line"
    _description = "Order Line for GB Others"

    def action_add_from_catalog(self):
        order = self.env['sale.order'].browse(self.env.context.get('order_id'))
        return order.with_context(aj_rub='gbot').action_add_from_catalog()

class GSADPAOrderLine(models.Model):
    _inherit = "opsol_ajmarine.inh_order_line"
    _name = "opsol_ajmarine.gsadpa_order_line"
    _description = "Order Line for GSAD Parts"

    def action_add_from_catalog(self):
        order = self.env['sale.order'].browse(self.env.context.get('order_id'))
        return order.with_context(aj_rub='gsadpa').action_add_from_catalog()


class GSADOTOrderLine(models.Model):
    _inherit = "opsol_ajmarine.inh_order_line"
    _name = "opsol_ajmarine.gsadot_order_line"
    _description = "Order Line for GSAD Others"

    def action_add_from_catalog(self):
        order = self.env['sale.order'].browse(self.env.context.get('order_id'))
        return order.with_context(aj_rub='gsadot').action_add_from_catalog()
