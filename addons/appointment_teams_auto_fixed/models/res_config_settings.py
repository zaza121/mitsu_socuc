from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    teams_enabled = fields.Boolean(string="Activer Teams pour les rendez-vous", config_parameter='appointment_teams_auto.teams_enabled', default=False)
    teams_tenant_id = fields.Char(string="Tenant ID", config_parameter='appointment_teams_auto.tenant_id')
    teams_client_id = fields.Char(string="Client ID", config_parameter='appointment_teams_auto.client_id')
    
    # Gestion sécurisée du secret via compute/inverse
    teams_client_secret = fields.Char(string="Client Secret", 
                                       compute='_compute_teams_client_secret', 
                                       inverse='_set_teams_client_secret') 
    
    teams_account_email = fields.Char(string="Compte (user) utilisé pour créer les réunions", config_parameter='appointment_teams_auto.account_email')
    teams_auto_create_user = fields.Boolean(string="Créer automatiquement un compte service (Azure AD)", default=False)
    teams_azure_primary_domain = fields.Char(string="Domaine Primaire Azure (onmicrosoft.com)", config_parameter='appointment_teams_auto.azure_primary_domain')


    def _compute_teams_client_secret(self):
        self.teams_client_secret = self.env['ir.config_parameter'].sudo().get_param('appointment_teams_auto.client_secret', default=False)

    def _set_teams_client_secret(self):
        IrConfig = self.env['ir.config_parameter'].sudo()
        if self.teams_client_secret:
            IrConfig.set_param('appointment_teams_auto.client_secret', self.teams_client_secret, group='base.group_system')
        else:
            IrConfig.unset_param('appointment_teams_auto.client_secret')
