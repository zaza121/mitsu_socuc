from odoo import models, fields, api
import io
import base64
import xlsxwriter
from datetime import date
from dateutil.relativedelta import relativedelta

class AuditGrandLivre(models.Model):
    _name = 'audit.grand.livre'
    _description = 'Audit Grand Livre SYSCOHADA'

    date = fields.Date("Date")
    compte = fields.Char("Compte")
    intitule = fields.Char("Intitulé")
    debit = fields.Monetary("Débit")
    credit = fields.Monetary("Crédit")
    type_anomalie = fields.Char("Type d’anomalie")
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)

    date_debut = fields.Date("Date de début")
    date_fin = fields.Date("Date de fin")

    classes_comptes = fields.Many2many(
        'account.account', 
        string="Comptes à auditer",
        help="Sélectionnez les comptes (ou codes de classes) à inclure dans l'audit."
    )

    export_file = fields.Binary("Fichier Excel", readonly=True)
    export_filename = fields.Char("Nom du fichier")

    # -------------------
    # Audit des écritures
    # -------------------
    def run_audit(self):
        # Par simplicité: purge toutes les anomalies existantes (dans ce modèle)
        self.env['audit.grand.livre'].search([]).unlink()

        # Filtrage par période
        domain = []
        if self.date_debut:
            domain.append(('date', '>=', self.date_debut))
        if self.date_fin:
            domain.append(('date', '<=', self.date_fin))

        # Filtrage par comptes sélectionnés
        if self.classes_comptes:
            account_ids = self.classes_comptes.ids
            domain.append(('account_id', 'in', account_ids))

        move_lines = self.env['account.move.line'].search(domain)

        anomalies_vals = []
        for line in move_lines:
            solde = (line.debit or 0.0) - (line.credit or 0.0)
            compte_code = line.account_id.code or ""
            intitule = line.name or line.move_id.ref or line.move_id.name or ""
            date_op = line.date

            # --- Règles SYSCOHADA classiques ---
            if compte_code.startswith("40") and solde > 0:
                anomalies_vals.append((date_op, compte_code, intitule, line.debit, line.credit, "Fournisseur débiteur"))
            if compte_code.startswith("41") and solde < 0:
                anomalies_vals.append((date_op, compte_code, intitule, line.debit, line.credit, "Client créditeur"))
            if compte_code.startswith("44") and abs(solde) > 1e-6:
                anomalies_vals.append((date_op, compte_code, intitule, line.debit, line.credit, "TVA non soldée"))
            if compte_code.startswith("5") and solde < 0:
                anomalies_vals.append((date_op, compte_code, intitule, line.debit, line.credit, "Trésorerie créditeur"))
            if compte_code.startswith("6") and solde < 0:
                anomalies_vals.append((date_op, compte_code, intitule, line.debit, line.credit, "Charge créditeur"))
            if compte_code.startswith("7") and solde > 0:
                anomalies_vals.append((date_op, compte_code, intitule, line.debit, line.credit, "Produit débiteur"))

        if anomalies_vals:
            for a in anomalies_vals:
                self.env['audit.grand.livre'].create({
                    'date': a[0],
                    'compte': a[1],
                    'intitule': a[2],
                    'debit': a[3],
                    'credit': a[4],
                    'type_anomalie': a[5],
                })
        else:
            self.env['audit.grand.livre'].create({
                'type_anomalie': "✅ Aucune anomalie détectée pour cette période et cette sélection de comptes"
            })
        return True

    def action_run_audit(self):
        return self.run_audit()

    # -------------------
    # Audit périodes automatiques
    # -------------------
    def audit_mois_courant(self):
        today = date.today()
        self.date_debut = today.replace(day=1)
        self.date_fin = (self.date_debut + relativedelta(months=1)) - relativedelta(days=1)
        return self.run_audit()

    def audit_trimestre_courant(self):
        today = date.today()
        month = ((today.month - 1)//3)*3 + 1
        self.date_debut = date(today.year, month, 1)
        self.date_fin = (self.date_debut + relativedelta(months=3)) - relativedelta(days=1)
        return self.run_audit()

    def audit_annee_courante(self):
        today = date.today()
        self.date_debut = date(today.year, 1, 1)
        self.date_fin = date(today.year, 12, 31)
        return self.run_audit()

    # -------------------
    # Export Excel
    # -------------------
    def export_to_excel(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet("Anomalies")

        bold = workbook.add_format({'bold': True})
        money_format = workbook.add_format({'num_format': '#,##0.00'})

        headers = ["Date", "Compte", "Intitulé", "Débit", "Crédit", "Type d’anomalie"]
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, bold)

        row_num = 1
        for anomaly in self.env['audit.grand.livre'].search([], order='date asc,id asc'):
            worksheet.write(row_num, 0, str(anomaly.date or ""))
            worksheet.write(row_num, 1, anomaly.compte or "")
            worksheet.write(row_num, 2, anomaly.intitule or "")
            worksheet.write_number(row_num, 3, float(anomaly.debit or 0), money_format)
            worksheet.write_number(row_num, 4, float(anomaly.credit or 0), money_format)
            worksheet.write(row_num, 5, anomaly.type_anomalie or "")
            row_num += 1

        workbook.close()
        output.seek(0)

        data = base64.b64encode(output.read())
        self.write({
            'export_file': data,
            'export_filename': 'Audit_Grand_Livre.xlsx'
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'audit.grand.livre',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
