from odoo import models, fields

class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'
    
    crm_lead_id = fields.Many2one('crm.lead', string="Opportunité CRM")