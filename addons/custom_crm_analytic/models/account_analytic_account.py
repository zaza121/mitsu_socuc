from odoo import models, fields

class AccountAnalyticAccount(models.Model):
_inherit = 'account.analytic.account'

# Champ inverse pour relier un compte analytique à une opportunité CRM
crm_lead_id = fields.Many2one('crm.lead', string="Opportunité CRM")