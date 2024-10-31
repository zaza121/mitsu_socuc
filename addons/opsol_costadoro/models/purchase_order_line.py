# -*- coding: utf-8 -*-
from datetime import timedelta

from odoo import api, fields, models
from odoo.addons.opsol_ajmarine.models.sale_order_line import INSTORE_SELECTION, INSTORE_ADDDAYS


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    in_store = fields.Selection(string="In Store", selection=INSTORE_SELECTION)
    aj_note = fields.Char(string='Note')
    aj_po_state = fields.Char(string="State char", compute="compute_aj_po_state", store=True)
    s_order_id = fields.Many2one(
        comodel_name='sale.order',
        compute="compute_infos",
        string='Sale Order',
        store=True
    )
    sale_partner_id = fields.Many2one(
        comodel_name='res.partner',
        compute="sale_partner_id",
        string='Client',
        store=True
    )
    sale_project_id = fields.Many2one(
        comodel_name='project.project',
        string='Projet Devis',
        compute="compute_infos",
        store=True
    )
    so_reference = fields.Char(
        string='Reference vente',
        compute="compute_so_reference",
        store=True,
        readonly=True
    )
    is_reman = fields.Boolean(
        string="Is Reman",
        compute="compute_so_reference",
        store=True,
        readonly=True
    )
    date_order = fields.Datetime(related="order_id.date_order")
    reman_state = fields.Selection(
        string="ETAT",
        selection=[
            ('cancel', 'CANCELLED'),
            ('en_cours', 'EN COURS'),
            ('return_cat', 'RETURNED CAT'),
            ('hold', 'HOLD AJ'),
            ('hold_customer', 'HOLD Customer'),
            ('return_nps', 'Returned NPS'),],
        default="",
        readonly=False,
    )
    return_n_type = fields.Selection(
        string='Return N type',
        selection=[('parts', 'PARTS'),('core', 'CORE')],
        default="",
    )
    return_n_qty = fields.Float(
        string='Return N Qty',
        default=0
    )
    return_date = fields.Date(
        string='Return Date'
    )
    return_ref = fields.Date(
        string='Return Ref'
    )
    # line_caution_ids = fields.One2many(
    #     comodel_name='opsol_ajmarine.reman_line',
    #     compute="compute_total_caution",
    #     string='Lignes cautions',
    #     store=True,
    # )
    caution_qty = fields.Float(
        string="CORE/PARTS Qty",
        compute="compute_total_caution",
        stored=True
    )
    amount_caution = fields.Monetary(
        string="CORE/PARTS Unit",
        compute="compute_total_caution",
        stored=True
    )
    total_caution = fields.Monetary(
        string="CORE/PARTS Total",
        compute="compute_total_caution",
        stored=True
    )
    invoice_id = fields.Many2one(
        comodel_name='account.move',
        string="Facture",
        compute="_get_invoice",
        copy=False
    )
    invoice_date = fields.Date(
        string='Date facture',
        compute="_get_invoice",
    )
    credit_qty = fields.Float(string='Credit Qty')
    credit_amount_caution = fields.Monetary(
        string="CORE/PARTS Unit",
        compute="compute_total_caution",
        stored=True
    )
    credit_note = fields.Char(
        string="Credit N°"
    )
    credit_note_date = fields.Date(
        string='Credit Date',
    )
    balance_status = fields.Float(
        string="Balance Status",
        compute="get_balance_values",
    )
    bal_amount_to_return = fields.Monetary(
        string='Amount to return',
        compute="get_balance_values",
    )
    bal_amount_due = fields.Monetary(
        string='Amount DUE',
        compute="get_balance_values",
    )
    bal_return_delay = fields.Integer(
        string='Return delay',
        compute="get_balance_values",
    )
    bal_credit_delay = fields.Integer(
        string='Credit delay',
        compute="get_balance_values",
    )
    remark = fields.Text(string='Remarks')
    n_catorder = fields.Char(string='N° CAT ORDER')

    @api.depends("order_id.state")
    def compute_aj_po_state(self):
        for rec in self:
            rec.aj_po_state = rec.order_id.state or ""

    @api.depends('reman_state', 'total_caution')
    def get_balance_values(self):
        for line in self:
            bal = line.total_caution
            line.balance_status = 0
            line.bal_amount_to_return = bal
            line.bal_amount_due = line.reman_state == 'return_cat' and bal or 0
            line.bal_return_delay = 0
            line.bal_credit_delay = 0

    def _get_invoice(self):
        for line in self:
            invoices = self.order_id._get_sale_orders().mapped("invoice_ids")
            line.invoice_id = invoices[0] if len(invoices) > 0 else None
            line.invoice_date = invoices[0].invoice_date if len(invoices) > 0 else None

    @api.depends('price_subtotal', 'state', 'reman_state')
    def compute_total_caution(self):
        sol_obj = self.env["sale.order.line"]
        for rec in self:

            if not rec.product_id:
                rec.total_caution = 0
                rec.caution_qty = 0
                rec.amount_caution = 0
                rec.credit_amount_caution = 0
            else:
                sale_orders = self.order_id._get_sale_orders()
                line_sale = sale_orders.mapped('order_line').filtered(lambda x : x.product_id and x.product_id.id == rec.product_id.id)
                lines_caution = line_sale.mapped('line_caution_ids')

                rec.total_caution = sum(lines_caution.mapped('total_caution'))
                rec.caution_qty = sum(lines_caution.mapped('qty'))
                rec.amount_caution = rec.total_caution / rec.caution_qty if rec.caution_qty else 0
                rec.credit_amount_caution = rec.total_caution / rec.caution_qty if rec.caution_qty else 0

    @api.depends('state')
    def compute_infos(self):
        sol_obj = self.env["sale.order.line"]
        for rec in self:

            if not rec.product_id:
                rec.s_order_id = False
                rec.sale_project_id = False
                rec.sale_partner_id = False
            else:
                sale_orders = self.order_id._get_sale_orders()
                line_sale = sale_orders.mapped('order_line').filtered(lambda x : x.product_id and x.product_id.id == rec.product_id.id)
                lines_caution = line_sale.mapped('line_caution_ids')

                rec.sale_partner_id = sale_orders and sale_orders[0].partner_id or False
                rec.sale_project_id = sale_orders and sale_orders.mapped("project_ids") and sale_orders.mapped("project_ids")[0] or False
                rec.s_order_id = sale_orders and sale_orders[0] or False

    @api.depends('product_id', 'state')
    def compute_so_reference(self):
        for rec in self:
            if rec.state in ['draft', 'sent']:
                rec.so_reference = rec.product_id and rec.product_id.default_code or ""
                rec.is_reman = rec.product_id and rec.product_id.is_reman or False
    
    @api.model
    def _prepare_purchase_order_line_from_procurement(self, product_id, product_qty, product_uom, company_id, values, po):
        res = super()._prepare_purchase_order_line_from_procurement(product_id, product_qty, product_uom, company_id, values, po)
        res.update({'in_store': values.get('in_store', False), 'aj_note': values.get('aj_note', "")})
        return res

    def _prepare_stock_move_vals(self, picking, price_unit, product_uom_qty, product_uom):
        res = super()._prepare_stock_move_vals(picking, price_unit, product_uom_qty, product_uom)
        date_planned = self.order_id.date_planned or self.date
        if self.in_store:
            date_planned += timedelta(days=INSTORE_ADDDAYS.get(self.in_store))
        res.update({'in_store': self.in_store,'aj_note': self.aj_note, 'date': date_planned,})
        return res
