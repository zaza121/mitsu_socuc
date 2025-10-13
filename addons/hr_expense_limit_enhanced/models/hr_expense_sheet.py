from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime

class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    def action_submit_sheet(self):
        for sheet in self:
            job = sheet.employee_id.job_id
            job_limit = job.expense_limit
            max_total = job.max_sheet_total
            tolerance = job.expense_limit_tolerance or 0.0

            # Vérifier le total par feuille
            if max_total > 0 and sheet.total_amount > max_total:
                raise ValidationError(
                    f"Le total des dépenses ({sheet.total_amount} €) dépasse le plafond par feuille ({max_total} €)."
                )

            # Vérifier la limite mensuelle
            emp = sheet.employee_id
            if emp.monthly_expense_limit > 0:
                start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
                domain = [
                    ('employee_id', '=', emp.id),
                    ('state', 'in', ['approve', 'done']),
                    ('date', '>=', start_date),
                ]
                expenses = self.env['hr.expense.sheet'].search(domain)
                total_month = sum(e.total_amount for e in expenses)
                if total_month + sheet.total_amount > emp.monthly_expense_limit:
                    raise ValidationError(
                        f"Plafond mensuel dépassé : {total_month + sheet.total_amount} € / {emp.monthly_expense_limit} €."
                    )

            # Vérification des lignes
            for expense in sheet.expense_line_ids:
                cat_limit = expense.product_id.expense_limit
                applicable_limits = [x for x in [job_limit, cat_limit] if x > 0]
                if applicable_limits:
                    applicable_limit = min(applicable_limits)
                    if expense.total_amount > applicable_limit:
                        if not expense.justification_text:
                            raise ValidationError(
                                f"La dépense '{expense.name}' dépasse la limite ({applicable_limit} €). Justification requise."
                            )
                        if expense.total_amount > applicable_limit * (1 + tolerance / 100):
                            raise ValidationError(
                                f"Dépassement supérieur à la tolérance pour '{expense.name}' (limite : {applicable_limit} € + {tolerance}%)."
                            )
        return super().action_submit_sheet()