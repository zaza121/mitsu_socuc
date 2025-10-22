# -- coding: utf-8 --

from odoo import models, fields, api, _
import io
import base64
import xlsxwriter
from datetime import date
from dateutil.relativedelta import relativedelta
from psycopg2.extensions import AsIs
from odoo.tools import float_is_zero


class AuditGrandLivre(models.TransientModel):
    _name = 'audit.grand.livre'
    _description = 'Audit Grand Livre SYSCOHADA (Optimisé)'

    # Champs d'affichage
    date = fields.Date("Date")
    compte = fields.Char("Compte")
    intitule = fields.Char("Intitulé")
    debit = fields.Monetary("Débit")
    credit = fields.Monetary("Crédit")
    type_anomalie = fields.Char("Type d’anomalie")
    currency_id = fields.Many2one('res.currency', string='Devise', default=lambda self: self.env.company.currency_id)

    # Champs de paramétrage
    date_debut = fields.Date("Date de début")
    date_fin = fields.Date("Date de fin")
    classes_comptes = fields.Many2many(
        'account.account',
        string="Classes de comptes à auditer",
        widget="many2many_tags",
        help="Sélectionnez les comptes ou classes de comptes à inclure dans l'audit."
    )

    export_file = fields.Binary("Fichier Excel", readonly=True)
    export_filename = fields.Char("Nom du fichier")

    # --------------------------
    # FONCTION : RUN AUDIT
    # --------------------------
    def run_audit(self):
        self.ensure_one()

        date_debut = self.date_debut
        date_fin = self.date_fin
        account_ids = self.classes_comptes.mapped('id')

        query_parts = []
        base_where = "am.state = 'posted' AND aml.date >= %s AND aml.date <= %s"
        account_filter_sql = ""
        account_params_tuple = ()

        if account_ids:
            account_filter_sql = "AND aml.account_id IN %s"
            account_params_tuple = (tuple(account_ids),)

        base_params = [date_debut, date_fin]

        # Règles SYSCOHADA
        query_parts.append(f"""
            SELECT aml.id, 'Fournisseur débiteur' AS anomaly_type
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            JOIN account_move am ON aml.move_id = am.id
            WHERE {base_where} AND aa.code LIKE '40%%' AND aml.debit > aml.credit {account_filter_sql}
        """)

        query_parts.append(f"""
            SELECT aml.id, 'Client créditeur' AS anomaly_type
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            JOIN account_move am ON aml.move_id = am.id
            WHERE {base_where} AND aa.code LIKE '41%%' AND aml.credit > aml.debit {account_filter_sql}
        """)

        query_parts.append(f"""
            SELECT aml.id, 'TVA non soldée' AS anomaly_type
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            JOIN account_move am ON aml.move_id = am.id
            WHERE {base_where} AND aa.code LIKE '44%%' AND aml.debit != aml.credit {account_filter_sql}
        """)

        query_parts.append(f"""
            SELECT aml.id, 'Trésorerie créditeur' AS anomaly_type
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            JOIN account_move am ON aml.move_id = am.id
            WHERE {base_where} AND aa.code LIKE '5%%' AND aml.credit > aml.debit {account_filter_sql}
        """)

        query_parts.append(f"""
            SELECT aml.id, 'Charge créditeur' AS anomaly_type
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            JOIN account_move am ON aml.move_id = am.id
            WHERE {base_where} AND aa.code LIKE '6%%' AND aml.credit > aml.debit {account_filter_sql}
        """)

        query_parts.append(f"""
            SELECT aml.id, 'Produit débiteur' AS anomaly_type
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            JOIN account_move am ON aml.move_id = am.id
            WHERE {base_where} AND aa.code LIKE '7%%' AND aml.debit > aml.credit {account_filter_sql}
        """)

        final_query = " UNION ALL ".join(query_parts)

        full_params = []
        for _ in range(len(query_parts)):
            full_params.extend(base_params)
            full_params.extend(account_params_tuple)

        self.env.cr.execute(final_query, full_params)
        anomaly_results = self.env.cr.fetchall()

        if anomaly_results:
            anomaly_ids = [r[0] for r in anomaly_results]
            anomaly_type_map = {r[0]: r[1] for r in anomaly_results}
            move_lines = self.env['account.move.line'].browse(anomaly_ids)

            results = [{
                'date': l.date,
                'compte': l.account_id.code,
                'intitule': l.name or l.move_id.ref,
                'debit': l.debit,
                'credit': l.credit,
                'type_anomalie': anomaly_type_map.get(l.id),
            } for l in move_lines]

            new_records = self.create(results)

            return {
                'type': 'ir.actions.act_window',
                'name': 'Résultats Audit Grand Livre',
                'res_model': self._name,
                'view_mode': 'list',
                'domain': [('id', 'in', new_records.ids)],
                'target': 'main',
            }
        else:
            self.write({'type_anomalie': "✅ Aucune anomalie détectée"})
            return {
                'type': 'ir.actions.act_window',
                'res_model': self._name,
                'view_mode': 'form',
                'res_id': self.id,
                'target': 'new',
            }

    def action_run_audit(self):
        return self.run_audit()

    # --------------------------
    # Périodes automatiques
    # --------------------------
    def _set_dates_and_return_form(self, debut, fin):
        self.ensure_one()
        self.write({
            'date_debut': debut,
            'date_fin': fin,
            'export_file': False,
            'type_anomalie': False,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

    def audit_mois_courant(self):
        today = date.today()
        debut = today.replace(day=1)
        fin = (debut + relativedelta(months=1)) - relativedelta(days=1)
        return self._set_dates_and_return_form(debut, fin)

    def audit_trimestre_courant(self):
        today = date.today()
        month = ((today.month - 1)//3)*3 + 1
        debut = date(today.year, month, 1)
        fin = (debut + relativedelta(months=3)) - relativedelta(days=1)
        return self._set_dates_and_return_form(debut, fin)

    def audit_annee_courante(self):
        today = date.today()
        debut = date(today.year, 1, 1)
        fin = date(today.year, 12, 31)
        return self._set_dates_and_return_form(debut, fin)

    # --------------------------
    # Export Excel
    # --------------------------
    def export_to_excel(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet("Anomalies")

        bold = workbook.add_format({'bold': True})
        money_fmt = workbook.add_format({'num_format': '#,##0.00'})

        headers = ["Date", "Compte", "Intitulé", "Débit", "Crédit", "Type d’anomalie"]
        for col, head in enumerate(headers):
            sheet.write(0, col, head, bold)

        domain = ['&', ('type_anomalie', '!=', False), ('id', '!=', self.id)]
        for row, rec in enumerate(self.search(domain), start=1):
            sheet.write(row, 0, str(rec.date or ""))
            sheet.write(row, 1, rec.compte or "")
            sheet.write(row, 2, rec.intitule or "")
            sheet.write_number(row, 3, rec.debit or 0, money_fmt)
            sheet.write_number(row, 4, rec.credit or 0, money_fmt)
            sheet.write(row, 5, rec.type_anomalie or "")

        workbook.close()
        output.seek(0)
        data = base64.b64encode(output.read())
        self.write({
            'export_file': data,
            'export_filename': 'Audit_Grand_Livre.xlsx',
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
