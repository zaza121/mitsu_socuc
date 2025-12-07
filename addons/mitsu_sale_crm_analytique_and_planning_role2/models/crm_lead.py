# -*- coding: utf-8 -*-
from odoo import api, fields, models, Command, _
from odoo.osv import expression
from odoo.exceptions import ValidationError
from datetime import datetime


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    distribution_id = fields.Many2one(
        comodel_name='account.analytic.distribution.model',
        string='Modele analytique',
    )
    account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Compte',
    )

    def _prepare_opportunity_quotation_context(self):
        quotation_context = super()._prepare_opportunity_quotation_context()
        if self.distribution_id:
            quotation_context['default_force_distribution_id'] = self.distribution_id.id
        return quotation_context
