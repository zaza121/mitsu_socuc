from odoo import models, _
from odoo.exceptions import UserError

class AccountMove(models.Model):
    _inherit = 'account.move'
    
    def _get_project_from_distribution(self, distribution):
        if not distribution:
            return False
        try:
            keys = list(distribution.keys())
        except Exception:
            return False
        if not keys:
            return False
        project = self.env['project.project'].search([
            ('analytic_account_id', 'in', keys)
        ], limit=1)
        return project
    
    def _check_internal_project_revenue(self):
        for move in self:
            if move.move_type in ('out_invoice', 'out_refund'):
                for line in move.invoice_line_ids:
                    dist = line.analytic_distribution if hasattr(line, 'analytic_distribution') else False
                    project = self._get_project_from_distribution(dist)
                    if project and project.project_type == 'internal':
                        raise UserError(_("Les projets internes ne peuvent pas générer de revenus (Factures Clients)."))