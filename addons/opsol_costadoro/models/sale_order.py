# -*- coding: utf-8 -*-

from odoo import api, fields, models, Command, _
from collections import defaultdict
import logging
import functools
import re
from odoo.exceptions import UserError, ValidationError
from datetime import date


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.constrains("state")
    def check_partner_end_date(self):
        today = date.today()
        for rec in self:
            if rec.state == "sale":
                date_end = rec.partner_id.date_fin
                if date_end and date_end < today:
                    raise ValidationError(_("La date de fin validite du client %(client)s est depassee", client=rec.partner_id.name))

    @api.constrains("partner_id")
    def add_partner_transport_fee(self):
        for rec in self:
            transport_line = rec.order_line.filtered(lambda x: x.is_transport_fee)
            factu_fee_line = rec.order_line.filtered(lambda x: x.is_facturation_fee)
            delete_lines = transport_line + factu_fee_line
            to_execute = [Command.delete(elt.id) for elt in delete_lines]

            if rec.partner_id and rec.partner_id.transport_product_id:
                prod = rec.partner_id.transport_product_id
                value = {
                    'product_id': prod.id, 'name': prod.name, 'product_uom_qty': 1, 'price_unit': rec.partner_id.transport_amount,
                    'is_transport_fee': True
                }
                to_execute.append(Command.create(value))
                
            if rec.partner_id and rec.partner_id.facturation_product_id:
                prod = rec.partner_id.facturation_product_id
                value = {
                    'product_id': prod.id, 'name': prod.name, 'product_uom_qty': 1, 'price_unit': rec.partner_id.transport_amount,
                    'is_facturation_fee': True
                }
                to_execute.append(Command.create(value))
            
            rec.update({'order_line': to_execute})
