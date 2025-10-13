# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.tools import SQL


class AccountInvoiceReport(models.Model):
    """Inherited account invoice report"""
    _inherit = 'account.invoice.report'

    margin_amount = fields.Float('Margin', readonly=True)

    @api.model
    def _select(self) -> SQL:
        """Adding the margin amount in the query """
        res = super(AccountInvoiceReport, self)._select()
        v_select = f"{res.code} , line.margin_amount * account_currency_table.rate AS margin_amount"
        return SQL(v_select)

