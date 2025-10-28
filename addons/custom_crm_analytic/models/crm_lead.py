from odoo import models, fields, api

class CrmLead(models.Model):
_inherit = 'crm.lead'

# On relie les comptes analytiques à l'opportunité (One2many inverse)
analytic_account_ids = fields.One2many(
'account.analytic.account',
'crm_lead_id',
string="Comptes Analytiques liés"
)

# Compte analytique principal
analytic_account_id = fields.Many2one(
'account.analytic.account',
string="Compte Analytique Principal"
)

def action_new_quotation(self):
action = super(CrmLead, self).action_new_quotation()
if isinstance(action, dict):
ctx = action.get('context') or {}
if self.analytic_account_id:
ctx = dict(ctx)
ctx['default_analytic_account_id'] = self.analytic_account_id.id
action['context'] = ctx
return action