# -- coding: utf-8 --
from odoo import models, fields, api, _
import io
import base64
import xlsxwriter
from datetime import date
from dateutil.relativedelta import relativedelta
from psycopg2.extensions import AsIs
from odoo.tools import float_is_zero
import logging

_logger = logging.getLogger(__name__)

class AuditGrandLivre(models.TransientModel):
    _name = 'audit.grand.livre'
    _description = 'Audit Grand Livre PCG Français (Optimisé)'

    # Champs d'affichage des résultats (utiles seulement dans la vue tree - Transient Model)
    date = fields.Date("Date")
    compte = fields.Char("Compte")
    intitule = fields.Char("Intitulé")
    debit = fields.Monetary("Débit")
    credit = fields.Monetary("Crédit")
    type_anomalie = fields.Char("Type d’anomalie")
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)

    # Champs de PARAMÈTRES
    date_debut = fields.Date("Date de début", required=True)
    date_fin = fields.Date("Date de fin", required=True)

    classes_comptes = fields.Many2many(
        'account.account',  
        string="Comptes à auditer",
        widget="many2many_tags",
        help="Sélectionnez les comptes ou classes de comptes à inclure dans l'audit"
    )

    export_file = fields.Binary("Fichier Excel", readonly=True)
    export_filename = fields.Char("Nom du fichier")

    # -------------------
    # Audit des écritures (OPTIMISÉ PCG POUR GRANDE VOLUMÉTRIE)
    # -------------------
    def run_audit(self):
        self.ensure_one()

        # 1. Préparation des paramètres
        date_debut = self.date_debut
        date_fin = self.date_fin
        account_ids = self.classes_comptes.mapped('id')
        
        # 2. Suppression des enregistrements d'anomalies précédents pour l'utilisateur
        # Suppression uniquement des enregistrements créés par le wizard actif (pour éviter d'effacer les résultats d'autres utilisateurs)
        self.search([('create_uid', '=', self.env.uid), ('type_anomalie', '!=', False)]).unlink()

        # 3. Construction de la requête SQL (Haute Performance)
        
        query_parts = []
        base_where = "am.state = 'posted' AND aml.date >= %s AND aml.date <= %s"
        
        # Le filtre de compte doit être intégré dans chaque règle pour une exécution propre
        account_filter_sql = ""
        account_params_tuple = ()

        if account_ids:
            # Sécurité: Ajout de %s pour être remplacé par le tuple des IDs de comptes
            account_filter_sql = "AND aml.account_id IN %s"
            account_params_tuple = (tuple(account_ids),)

        # Les paramètres de base pour chaque requête (date_debut, date_fin)
        base_params = [date_debut, date_fin]

        # Fonction utilitaire pour assembler les parties de la requête et les paramètres
        def _get_query_and_params(rule_where, anomaly_type):
            query = f"""
                SELECT aml.id, '{anomaly_type}' AS anomaly_type
                FROM account_move_line aml
                JOIN account_account aa ON aml.account_id = aa.id
                JOIN account_move am ON aml.move_id = am.id
                WHERE {base_where}
                AND {rule_where}
                {account_filter_sql}
            """
            params = base_params + list(account_params_tuple)
            return query, params

        # RÈGLE 1: Classe 1 (Capitaux) - Solde naturel Créditeur (Anomaly: Debit > Credit)
        query_parts.append(_get_query_and_params("aa.code LIKE '1%%' AND aml.debit > aml.credit", 
                                                'Capitaux anormalement débiteur (PCG 1)'))

        # RÈGLE 2: Classe 2 & 3 (Actif Immo & Stocks) - Solde naturel Débiteur (Anomaly: Credit > Debit)
        query_parts.append(_get_query_and_params("(aa.code LIKE '2%%' OR aa.code LIKE '3%%') AND aml.credit > aml.debit", 
                                                'Actif anormalement créditeur (PCG 2/3)'))

        # RÈGLE 3: Classe 40 (Fournisseurs) - Solde naturel Créditeur (Anomaly: Debit > Credit)
        query_parts.append(_get_query_and_params("aa.code LIKE '40%%' AND aml.debit > aml.credit", 
                                                'Compte Fournisseur débiteur (PCG 40)'))

        # RÈGLE 4: Classe 41 (Clients) - Solde naturel Débiteur (Anomaly: Credit > Debit)
        query_parts.append(_get_query_and_params("aa.code LIKE '41%%' AND aml.credit > aml.debit", 
                                                'Compte Client créditeur (PCG 41)'))

        # RÈGLE 5: Classe 44 (État/Taxes) - Ligne non soldée (Anomaly: Debit != Credit)
        # Note: Cette règle vérifie chaque ligne, pas l'équilibre du compte, ce qui est une bonne approche pour le Grand Livre.
        query_parts.append(_get_query_and_params("aa.code LIKE '44%%' AND aml.debit != aml.credit", 
                                                'TVA/État non soldée (PCG 44)'))
        
        # RÈGLE 6: Classe 5 (Trésorerie) - Solde naturel Débiteur (Anomaly: Credit > Debit)
        query_parts.append(_get_query_and_params("aa.code LIKE '5%%' AND aml.credit > aml.debit", 
                                                'Trésorerie anormalement créditeur (PCG 5)'))

        # RÈGLE 7: Classe 6 (Charges) - Solde naturel Débiteur (Anomaly: Credit > Debit)
        query_parts.append(_get_query_and_params("aa.code LIKE '6%%' AND aml.credit > aml.debit", 
                                                'Charge anormalement créditrice (PCG 6)'))

        # RÈGLE 8: Classe 7 (Produits) - Solde naturel Créditeur (Anomaly: Debit > Credit)
        query_parts.append(_get_query_and_params("aa.code LIKE '7%%' AND aml.debit > aml.credit", 
                                                'Produit anormalement débiteur (PCG 7)'))
        
        # Assemblage final de la requête avec UNION ALL
        final_query_list = [qp[0] for qp in query_parts]
        final_query = " UNION ALL ".join(final_query_list)
        
        # Préparation de la liste complète des paramètres pour execute()
        full_params = []
        for qp in query_parts:
            # Répéter les paramètres de date (2) et les paramètres de comptes (s'ils existent) pour chaque UNION
            full_params.extend(qp[1])

        _logger.info("Executing SQL Query: %s", final_query)
        _logger.info("With Parameters: %s", full_params)
        
        # 4. Exécution de la requête SQL
        try:
            self.env.cr.execute(final_query, full_params)
            anomaly_results = self.env.cr.fetchall() 
        except Exception as e:
            _logger.error("SQL Execution Failed: %s", e)
            raise

        # 5. Création des enregistrements de RÉSULTAT
        if anomaly_results:
            anomaly_ids = [res[0] for res in anomaly_results]
            anomaly_type_map = {res[0]: res[1] for res in anomaly_results}
            
            # Utilisation d'une seule requête browse pour optimiser
            move_lines = self.env['account.move.line'].browse(anomaly_ids)

            # Création des enregistrements Transient
            results_to_create = []
            
            for line in move_lines:
                results_to_create.append({
                    'date': line.date,
                    'compte': line.account_id.code,
                    'intitule': line.name if line.name else line.move_id.ref,
                    'debit': line.debit,
                    'credit': line.credit,
                    'type_anomalie': anomaly_type_map.get(line.id, 'Anomalie détectée'),
                    'currency_id': line.company_id.currency_id.id,
                })

            if results_to_create:
                # Mise à jour du premier enregistrement pour s'assurer que l'ID de l'action pointe dessus
                # Ceci est fait pour garantir le bon affichage dans l'action, même si le wizard est multi-enregistrement
                self.write(results_to_create[0]) 
                # Création des enregistrements suivants 
                if len(results_to_create) > 1:
                    self.create(results_to_create[1:])
        else:
            # Création d'un enregistrement 'placeholder' pour le message de succès (sur l'enregistrement actuel)
            self.write({
                'type_anomalie': "✅ Aucune anomalie détectée pour cette période et cette sélection de comptes",
                'date': date.today(),
            })
            
        # 6. Retourner l'action pour afficher les résultats dans la vue Tree
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'tree,form',
            'views': [(False, 'tree'), (False, 'form')],
            'domain': [('create_uid', '=', self.env.uid), ('id', '!=', self.id)], # Afficher les NOUVEAUX résultats
            'target': 'main', # Afficher les résultats dans la fenêtre principale
        }

    @api.model
    def action_run_audit(self):
        """Action liée au bouton dans la vue Form, appelle run_audit sur l'enregistrement actif."""
        return self.run_audit()

    # -------------------
    # Audit périodes automatiques
    # -------------------
    def _set_dates_and_return_form(self, date_debut, date_fin):
        self.ensure_one()
        self.write({
            'date_debut': date_debut,
            'date_fin': date_fin,
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
        # Correction pour calculer le premier mois du trimestre
        month = ((today.month - 1) // 3) * 3 + 1
        date_debut = date(today.year, month, 1)
        date_fin = (date_debut + relativedelta(months=3)) - relativedelta(days=1)
        return self._set_dates_and_return_form(date_debut, date_fin)

    def audit_annee_courante(self):
        today = date.today()
        date_debut = date(today.year, 1, 1)
        date_fin = date(today.year, 12, 31)
        return self._set_dates_and_return_form(date_debut, date_fin)

    # -------------------
    # Export Excel 
    # -------------------
    def export_to_excel(self):
        self.ensure_one()
        # Récupération des anomalies créées par le wizard pour l'utilisateur
        anomalies = self.search([('create_uid', '=', self.env.uid), ('type_anomalie', '!=', False), ('id', '!=', self.id)])

        if not anomalies and self.type_anomalie and self.type_anomalie.startswith('✅'):
             # Si seule la ligne de message de succès existe (l'enregistrement du wizard)
             raise models.UserError(_("Aucune anomalie à exporter. L'audit a réussi sans détecter d'anomalie."))
        
        if not anomalies:
            raise models.UserError(_("Aucune anomalie à exporter. Veuillez lancer l'audit avant d'exporter."))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet("Anomalies")

        bold = workbook.add_format({'bold': True, 'bg_color': '#D9D9D9'})
        money_format = workbook.add_format({'num_format': '#,##0.00'})

        # Définition des largeurs de colonnes
        worksheet.set_column('A:A', 10)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:C', 40)
        worksheet.set_column('D:E', 15)
        worksheet.set_column('F:F', 40)


        headers = ["Date", "Compte", "Intitulé", "Débit", "Crédit", "Type d’anomalie"]
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header, bold)

        rows_to_export = anomalies

        for row_num, anomaly in enumerate(rows_to_export, start=1):
            worksheet.write(row_num, 0, str(anomaly.date or ""))
            worksheet.write(row_num, 1, anomaly.compte or "")
            worksheet.write(row_num, 2, anomaly.intitule or "")
            worksheet.write_number(row_num, 3, anomaly.debit or 0, money_format)
            worksheet.write_number(row_num, 4, anomaly.credit or 0, money_format)
            worksheet.write(row_num, 5, anomaly.type_anomalie or "")

        workbook.close()
        output.seek(0)

        data = base64.b64encode(output.read())
        
        # Mise à jour du wizard pour permettre le téléchargement immédiat
        self.write({
            'export_file': data,
            'export_filename': 'Audit_Grand_Livre_PCG.xlsx'
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'audit.grand.livre',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }