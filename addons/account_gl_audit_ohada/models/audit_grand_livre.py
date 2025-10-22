# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import io, base64, xlsxwriter
from datetime import date
from dateutil.relativedelta import relativedelta

class AuditGrandLivre(models.TransientModel):
    _name = 'audit.grand.livre'
    _description = 'Audit Grand Livre SYSCOHADA (Optimisé)'

    date = fields.Date("Date")
    compte = fields.Char("Compte")
    intitule = fields.Char("Intitulé")
    debit = fields.Monetary("Débit")
    credit = fields.Monetary("Crédit")
    type_anomalie = fields.Char("Type d’anomalie")
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    date_debut = fields.Date("Date de début")
    date_fin = fields.Date("Date de fin")
    classes_comptes = fields.Many2many('account.account', string="Classes de comptes à auditer")
    export_file = fields.Binary("Fichier Excel", readonly=True)
    export_filename = fields.Char("Nom du fichier")

    def run_audit(self):
        self.ensure_one()
        date_debut, date_fin = self.date_debut, self.date_fin
        account_ids = self.classes_comptes.mapped('id')
        self.search([('type_anomalie', '!=', False)]).unlink()
        query_parts = []
        base_where = "am.state = 'posted' AND aml.date >= %s AND aml.date <= %s"
        account_filter_sql = "AND aml.account_id IN %s" if account_ids else ""
        account_params_tuple = (tuple(account_ids),) if account_ids else ()
        base_params = [date_debut, date_fin]
        rules = [
            ("40%%", "Fournisseur débiteur", "aml.debit > aml.credit"),
            ("41%%", "Client créditeur", "aml.credit > aml.debit"),
            ("44%%", "TVA non soldée (Anomalie)", "aml.debit != aml.credit"),
            ("5%%", "Trésorerie créditeur", "aml.credit > aml.debit"),
            ("6%%", "Charge créditeur", "aml.credit > aml.debit"),
            ("7%%", "Produit débiteur", "aml.debit > aml.credit"),
        ]
        for code_like, label, condition in rules:
            query_parts.append(f"""
                SELECT aml.id, '{label}' AS anomaly_type
                FROM account_move_line aml
                JOIN account_account aa ON aml.account_id = aa.id
                JOIN account_move am ON aml.move_id = am.id
                WHERE {base_where} AND aa.code LIKE '{code_like}' AND {condition} {account_filter_sql}
            """)
        final_query = " UNION ALL ".join(query_parts)
        full_params = []
        for _ in range(len(query_parts)):
            full_params.extend(base_params)
            full_params.extend(account_params_tuple)
        self.env.cr.execute(final_query, full_params)
        results = self.env.cr.fetchall()
        if results:
            ids = [r[0] for r in results]
            mapping = {r[0]: r[1] for r in results}
            lines = self.env['account.move.line'].browse(ids)
            vals = [{
                'date': l.date, 'compte': l.account_id.code, 'intitule': l.name or l.move_id.ref,
                'debit': l.debit, 'credit': l.credit, 'type_anomalie': mapping.get(l.id)
            } for l in lines]
            self.create(vals)
        else:
            self.create({'type_anomalie': "✅ Aucune anomalie détectée"})
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'tree,form',
            'target': 'main',
        }

    def export_to_excel(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        ws = workbook.add_worksheet("Anomalies")
        bold = workbook.add_format({'bold': True})
        money = workbook.add_format({'num_format': '#,##0.00'})
        headers = ["Date","Compte","Intitulé","Débit","Crédit","Type d’anomalie"]
        for i, h in enumerate(headers): ws.write(0, i, h, bold)
        for row, rec in enumerate(self.search([('type_anomalie', '!=', False)]), 1):
            ws.write(row,0,str(rec.date or "")); ws.write(row,1,rec.compte or "")
            ws.write(row,2,rec.intitule or ""); ws.write_number(row,3,rec.debit or 0,money)
            ws.write_number(row,4,rec.credit or 0,money); ws.write(row,5,rec.type_anomalie or "")
        workbook.close()
        output.seek(0)
        self.write({'export_file': base64.b64encode(output.read()), 'export_filename': 'Audit_Grand_Livre.xlsx'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }
