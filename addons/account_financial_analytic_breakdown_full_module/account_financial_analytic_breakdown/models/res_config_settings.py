from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    analytic_financial_breakdown_enabled = fields.Boolean(
        string="Enable analytic breakdown in financial reports",
        config_parameter='account_financial_analytic_breakdown.enabled'
    )
    analytic_financial_plan_id = fields.Many2one(
        string="Analytic plan for financial breakdown",
        comodel_name='account.analytic.plan',
        config_parameter='account_financial_analytic_breakdown.plan_id'
    )
    analytic_show_total_column = fields.Boolean(
        string="Show total analytic column",
        config_parameter='account_financial_analytic_breakdown.show_total'
    )
