# -- coding: utf-8 --

from odoo import models, fields, api, _
import io
import base64
import xlsxwriter
from datetime import date
from dateutil.relativedelta import relativedelta
from psycopg2.extensions import AsIs # Import non utilisé mais laissé pour la note de sécurité
from odoo.tools import float_is_zero

class AuditGrandLivre(models.TransientModel):
    _name = 'audit.grand.livre'
    _description = 'Audit Grand Livre SYSCOHADA (Optimisé)'

    # Champs d'affichage des résultats (utiles seulement dans la vue tree)
    date = fields.Date("Date")
    compte = fields.Char("Compte")
    intitule = fields.Char("Intitulé")
    debit = fields.Monetary("Débit")
    credit = fields.Monetary("Crédit")
    type_anomalie = fields.Char("Type d’anomalie")
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)

    # Champs de PARAMÈTRES (stockés sur le record actif)
    date_debut = fields.Date("Date de début")
    date_fin = fields.Date("Date de fin")

    classes_comptes = fields.Many2many(
        'account.account', 
        string="Classes de comptes à auditer",
        widget="many2many_tags",
        help="Sélectionnez les comptes ou classes de comptes à inclure dans l'audit"
    )

    export_file = fields.Binary("Fichier Excel", readonly=True)
    export_filename = fields.Char("Nom du fichier")

    #-------------------
    # Audit des écritures (OPTIMISÉ POUR GRANDE VOLUMÉTRIE)
    #-------------------
    def run_audit(self):
        self.ensure_one()

        # 1. Préparation des paramètres
        date_debut = self.date_debut
        date_fin = self.date_fin
        
        # Récupération des IDs des comptes filtrés par l'utilisateur
        account_ids = self.classes_comptes.mapped('id')
        
        # 2. Suppression des enregistrements d'anomalies précédents
        # Ce TransientModel est réutilisé pour l'affichage de l'audit.

        # 3. Construction de la requête SQL (Haute Performance)
        query_parts = []
        
        # La clause WHERE commune à toutes les règles (pièces postées + période)
        base_where = "am.state = 'posted' AND aml.date >= %s AND aml.date <= %s"
        
        # Création du filtre de compte SQL et des paramètres correspondants
        account_filter_sql = ""
        account_params_tuple = ()

        if account_ids:
            # Utilisation de la clause IN SQL pour filtrer les IDs
            account_filter_sql = "AND aml.account_id IN %s"
            account_params_tuple = (tuple(account_ids),)

        # Liste des paramètres de base [date_debut, date_fin]
        base_params = [date_debut, date_fin]

        # RÈGLE 1: Classe 40 (Fournisseurs) Débiteur (debit > credit)
        query_parts.append(f"""
            SELECT aml.id, 'Fournisseur débiteur' AS anomaly_type
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            JOIN account_move am ON aml.move_id = am.id
            WHERE {base_where} 
            AND aa.code LIKE '40%%'
            AND aml.debit > aml.credit 
            {account_filter_sql}
        """)

        # RÈGLE 2: Classe 41 (Clients) Créditeur (credit > debit)
        query_parts.append(f"""
            SELECT aml.id, 'Client créditeur' AS anomaly_type
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            JOIN account_move am ON aml.move_id = am.id
            WHERE {base_where} 
            AND aa.code LIKE '41%%'
            AND aml.credit > aml.debit
            {account_filter_sql}
        """)

        # RÈGLE 3: Classe 44 (TVA) Solde non nul (debit != credit)
        query_parts.append(f"""
            SELECT aml.id, 'TVA non soldée (Anomalie)' AS anomaly_type
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            JOIN account_move am ON aml.move_id = am.id
            WHERE {base_where} 
            AND aa.code LIKE '44%%'
            AND aml.debit != aml.credit 
            {account_filter_sql}
        """)
        
        # RÈGLE 4: Classe 5 (Trésorerie) Créditeur (credit > debit)
        query_parts.append(f"""
            SELECT aml.id, 'Trésorerie créditeur' AS anomaly_type
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            JOIN account_move am ON aml.move_id = am.id
            WHERE {base_where} 
            AND aa.code LIKE '5%%'
            AND aml.credit > aml.debit
            {account_filter_sql}
        """)

        # RÈGLE 5: Classe 6 (Charges) Créditeur (credit > debit)
        query_parts.append(f"""
            SELECT aml.id, 'Charge créditeur' AS anomaly_type
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            JOIN account_move am ON aml.move_id = am.id
            WHERE {base_where} 
            AND aa.code LIKE '6%%'
            AND aml.credit > aml.debit
            {account_filter_sql}
        """)

        # RÈGLE 6: Classe 7 (Produits) Débiteur (debit > credit)
        query_parts.append(f"""
            SELECT aml.id, 'Produit débiteur' AS anomaly_type
            FROM account_move_line aml
            JOIN account_account aa ON aml.account_id = aa.id
            JOIN account_move am ON aml.move_id = am.id
            WHERE {base_where} 
            AND aa.code LIKE '7%%'
            AND aml.debit > aml.credit
            {account_filter_sql}
        """)
        
        # Assemblage final de la requête avec UNION ALL
        final_query = " UNION ALL ".join(query_parts)
        
        # Préparation de la liste complète des paramètres pour execute()
        full_params = []
        num_rules = len(query_parts)
        for _ in range(num_rules):
            full_params.extend(base_params)
            full_params.extend(account_params_tuple) # Ajout du tuple si non vide

        # 4. Exécution de la requête SQL
        self.env.cr.execute(final_query, full_params)
        anomaly_results = self.env.cr.fetchall() # Récupère [ (id, type_anomalie), (id, type_anomalie), ... ]
        
        # 5. Création des enregistrements de RÉSULTAT
        if anomaly_results:
            anomaly_ids = [res[0] for res in anomaly_results]
            anomaly_type_map = {res[0]: res[1] for res in anomaly_results}
            
            # Charger les enregistrements d'anomalies en une seule fois
            move_lines = self.env['account.move.line'].browse(anomaly_ids)

            results_to_create = []
            for line in move_lines:
                compte = line.account_id.code
                intitule = line.name if line.name else line.move_id.ref
                
                results_to_create.append({
                    'date': line.date,
                    'compte': compte,
                    'intitule': intitule,
                    'debit': line.debit,
                    'credit': line.credit,
                    'type_anomalie': anomaly_type_map.get(line.id, 'Anomalie détectée'),
                })

            # Création massive des résultats (très rapide)
            new_results = self.create(results_to_create)
            
            # 6. Retourner l'action pour afficher les résultats dans la vue Tree
            return {
                'type': 'ir.actions.act_window',
                'name': 'Résultats de l\'Audit',
                'res_model': self._name,
                'view_mode': 'tree',
                # On filtre sur les résultats créés pour ne pas afficher les paramètres
                'domain': [('id', 'in', new_results.ids)],
                'target': 'main',
            }
        else:
            # Si aucune anomalie, on retourne le formulaire avec un message
            self.write({
                'type_anomalie': "✅ Aucune anomalie détectée pour cette période et cette sélection de comptes"
            })
            return {
                'type': 'ir.actions.act_window',
                'name': 'Audit Grand Livre',
                'res_model': self._name,
                'view_mode': 'form',
                'res_id': self.id,
                'target': 'new',
            }

    def action_run_audit(self):
        return self.run_audit()

    #-------------------
    # Audit périodes automatiques
    #-------------------
    def _set_dates_and_return_form(self, date_debut, date_fin):
        self.ensure_one()
        self.write({
            'date_debut': date_debut,
            'date_fin': date_fin,
            'export_file': False, # Réinitialise l'export
            'type_anomalie': False, # Cache le message de non-anomalie
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
        date_debut = today.replace(day=1)
        date_fin = (date_debut + relativedelta(months=1)) - relativedelta(days=1)
        return self._set_dates_and_return_form(date_debut, date_fin)

    def audit_trimestre_courant(self):
        today = date.today()
        month = ((today.month - 1)//3)*3 + 1
        date_debut = date(today.year, month, 1)
        date_fin = (date_debut + relativedelta(months=3)) - relativedelta(days=1)
        return self._set_dates_and_return_form(date_debut, date_fin)

    def audit_annee_courante(self):
        today = date.today()
        date_debut = date(today.year, 1, 1)
        date_fin = date(today.year, 12, 31)
        return self._set_dates_and_return_form(date_debut, date_fin)

    #-------------------
    # Export Excel 
    #-------------------
    def export_to_excel(self):
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet("Anomalies")

        bold = workbook.add_format({'bold': True})
        money_format = workbook.add_format({'num_format': '#,##0.00'})

        headers = ["Date", "Compte", "Intitulé", "Débit", "Crédit", "Type d’anomalie"]
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, bold)

        # Recherche des enregistrements de résultats (anomalies) créés par run_audit
        # On ne prend que les records qui ne sont pas l'instance de paramétrage courante
        domain = ['&', ('type_anomalie', '!=', False), ('id', '!=', self.id)]
        
        for row_num, anomaly in enumerate(self.search(domain), start=1):
            worksheet.write(row_num, 0, str(anomaly.date or ""))
            worksheet.write(row_num, 1, anomaly.compte or "")
            worksheet.write(row_num, 2, anomaly.intitule or "")
            worksheet.write_number(row_num, 3, anomaly.debit or 0, money_format)
            worksheet.write_number(row_num, 4, anomaly.credit or 0, money_format)
            worksheet.write(row_num, 5, anomaly.type_anomalie or "")

        workbook.close()
        output.seek(0)

        data = base64.b64encode(output.read())
        self.write({
            'export_file': data,
            'export_filename': 'Audit_Grand_Livre.xlsx'
        })

        # Retourne le formulaire pour permettre le téléchargement immédiat
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'audit.grand.livre',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }