from odoo import models, fields, api
import io
import base64
import xlsxwriter
from datetime import date
from dateutil.relativedelta import relativedelta

class AuditGrandLivre(models.Model):
    _name = 'audit.grand.livre'
    _description = 'Audit Grand Livre SYSCOHADA'

    # Champs pour les résultats
    date = fields.Date("Date")
    compte = fields.Char("Compte")
    intitule = fields.Char("Intitulé")
    debit = fields.Monetary("Débit")
    credit = fields.Monetary("Crédit")
    type_anomalie = fields.Char("Type d’anomalie")
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)

    # Champs pour les paramètres de l'audit
    date_debut = fields.Date("Date de début")
    date_fin = fields.Date("Date de fin")
    classes_comptes = fields.Many2many(
        'account.account',
        string="Classes de comptes à auditer",
        widget="many2many_tags",
        help="Sélectionnez les comptes ou classes de comptes à inclure dans l'audit"
    )

    # Champs pour l'export
    export_file = fields.Binary("Fichier Excel", readonly=True)
    export_filename = fields.Char("Nom du fichier")

    # -------------------
    # Logique d'audit
    # -------------------

    def _execute_audit_logic(self, current_audit):
        """ Logique principale de l'audit appliquée à l'enregistrement `current_audit` (SYSCOHADA). """
        
        # 1. Préparation du filtre des écritures comptables
        domain = []
        if current_audit.date_debut:
            domain.append(('date', '>=', current_audit.date_debut))
        if current_audit.date_fin:
            domain.append(('date', '<=', current_audit.date_fin))

        if current_audit.classes_comptes:
            account_ids = current_audit.classes_comptes.mapped('id')
            domain.append(('account_id', 'in', account_ids))

        move_lines = self.env['account.move.line'].search(domain)
        anomalies_data = []

        for line in move_lines:
            solde = line.debit - line.credit
            compte = line.account_id.code
            intitule = line.name
            date_op = line.date

            # ----------------------------------------------------------------------
            # --- RÈGLES D'AUDIT SYSCOHADA RÉVISÉ (Sens du solde) ---
            # ----------------------------------------------------------------------
            
            # Classe 1 (Ressources Stables / Passif) : Anomalie si Débiteur (solde > 0) [cite: 91, 92, 93]
            if compte.startswith("1") and solde > 0:
                anomalies_data.append((date_op, compte, intitule, line.debit, line.credit, "Classe 1 débitrice (Passif)"))

            # Classe 2 (Actif Immobilisé / Actif) : Anomalie si Créditeur (solde < 0) [cite: 94, 95, 96]
            if compte.startswith("2") and solde < 0:
                anomalies_data.append((date_op, compte, intitule, line.debit, line.credit, "Classe 2 créditrice (Actif)"))

            # Classe 3 (Stocks / Actif) : Anomalie si Créditeur (solde < 0) [cite: 97, 98, 99]
            if compte.startswith("3") and solde < 0:
                anomalies_data.append((date_op, compte, intitule, line.debit, line.credit, "Classe 3 créditrice (Stock)"))

            # Classe 4 (Tiers / Mixte) : Vérifications spécifiques
            # Classe 40 (Fournisseurs / Passif) : Anomalie si Débiteur [cite: 101, 102, 103]
            if compte.startswith("40") and solde > 0:
                anomalies_data.append((date_op, compte, intitule, line.debit, line.credit, "Fournisseur débiteur (Anomalie de solde)"))

            # Classe 41 (Clients / Actif) : Anomalie si Créditeur [cite: 104, 105, 106]
            if compte.startswith("41") and solde < 0:
                anomalies_data.append((date_op, compte, intitule, line.debit, line.credit, "Client créditeur (Anomalie de solde)"))
                
            # Classe 44 (Taxes / Mixte) : Anomalie si solde non nul [cite: 107, 108, 109]
            if compte.startswith("44") and solde != 0:
                anomalies_data.append((date_op, compte, intitule, line.debit, line.credit, "Classe 44 solde non nul (TVA non soldée)"))

            # Classe 5 (Trésorerie / Actif) : Anomalie si Créditeur [cite: 110, 111, 112]
            if compte.startswith("5") and solde < 0:
                anomalies_data.append((date_op, compte, intitule, line.debit, line.credit, "Trésorerie créditrice (Erreur de caisse/banque)"))

            # Classe 6 (Charges) : Anomalie si Créditeur (solde < 0) [cite: 113, 114, 115]
            if compte.startswith("6") and solde < 0:
                anomalies_data.append((date_op, compte, intitule, line.debit, line.credit, "Charge créditrice (Erreur de saisie)"))

            # Classe 7 (Produits) : Anomalie si Débiteur (solde > 0) [cite: 116, 117, 118]
            if compte.startswith("7") and solde > 0:
                anomalies_data.append((date_op, compte, intitule, line.debit, line.credit, "Produit débiteur (Erreur de saisie)"))

            # Classe 8 (Résultat / Affectation) : Anomalie si Solde Non Nul [cite: 119, 120, 121]
            if compte.startswith("8") and solde != 0:
                anomalies_data.append((date_op, compte, intitule, line.debit, line.credit, "Classe 8 solde non nul (Résultat/Affectation non soldé)"))

            # Classe 9 (Engagements Hors Bilan) : Anomalie si Solde Non Nul [cite: 122, 123, 124]
            if compte.startswith("9") and solde != 0:
                anomalies_data.append((date_op, compte, intitule, line.debit, line.credit, "Classe 9 solde non nul (Hors Bilan)"))

        # 2. Création des enregistrements d'anomalies
        if anomalies_data:
            for a in anomalies_data:
                self.create({
                    'date': a[0],
                    'compte': a[1],
                    'intitule': a[2],
                    'debit': a[3],
                    'credit': a[4],
                    'type_anomalie': a[5],
                })
        else:
            self.create({
                'type_anomalie': "✅ Aucune anomalie détectée pour cette période et cette sélection de comptes"
            })
            
        return current_audit.id


    def run_audit(self):
        """ Crée un nouvel enregistrement pour l'audit, lance la logique et affiche le résultat. """

        # Correction de l'erreur "Enregistrement manquant" : Supprime les anciens rapports, pas celui en cours [cite: 143, 144, 145]
        self.search([('id', '!=', self.id)]).unlink() 

        # Création du NOUVEL enregistrement pour l'affichage [cite: 146, 148, 149, 150, 151]
        new_audit = self.create({
            'date_debut': self.date_debut,
            'date_fin': self.date_fin,
            'classes_comptes': [(6, 0, self.classes_comptes.ids)],
        })
        
        self._execute_audit_logic(new_audit) [cite: 154]

        # Retourne l'action pour afficher le NOUVEL enregistrement [cite: 156, 157, 158, 159, 160, 161]
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'audit.grand.livre',
            'view_mode': 'tree,form',
            'res_id': new_audit.id,
            'target': 'main',
        }

    def action_run_audit(self):
        """ Bouton 'Lancer l'audit' """
        return self.run_audit() [cite: 164, 165]

    # Méthodes de période (CORRIGÉES pour créer un nouvel enregistrement)
    def audit_mois_courant(self):
        today = date.today() [cite: 170]
        date_debut = today.replace(day=1) [cite: 171]
        date_fin = (date_debut + relativedelta(months=1)) - relativedelta(days=1) [cite: 172]
        
        new_audit = self.create({
            'date_debut': date_debut,
            'date_fin': date_fin,
            'classes_comptes': [(6, 0, self.classes_comptes.ids)],
        }) [cite: 174, 175, 176, 177]
        return new_audit.run_audit() [cite: 179]

    def audit_trimestre_courant(self):
        today = date.today() [cite: 181]
        month = ((today.month - 1)//3)*3 + 1 [cite: 182]
        date_debut = date(today.year, month, 1) [cite: 183]
        date_fin = (date_debut + relativedelta(months=3)) - relativedelta(days=1) [cite: 184]
        
        new_audit = self.create({
            'date_debut': date_debut,
            'date_fin': date_fin,
            'classes_comptes': [(6, 0, self.classes_comptes.ids)],
        }) [cite: 185, 186, 187, 188]
        return new_audit.run_audit() [cite: 190]

    def audit_annee_courante(self):
        today = date.today() [cite: 192]
        date_debut = date(today.year, 1, 1) [cite: 193]
        date_fin = date(today.year, 12, 31) [cite: 194]
        
        new_audit = self.create({
            'date_debut': date_debut,
            'date_fin': date_fin,
            'classes_comptes': [(6, 0, self.classes_comptes.ids)],
        }) [cite: 195, 196, 197, 198]
        return new_audit.run_audit() [cite: 200]

    # Export Excel (Logique conservée)
    def export_to_excel(self):
        output = io.BytesIO() [cite: 205]
        workbook = xlsxwriter.Workbook(output, {'in_memory': True}) [cite: 206]
        worksheet = workbook.add_worksheet("Anomalies") [cite: 207]
        
        # ... (Logique d'écriture des en-têtes et des lignes) ...

        for row_num, anomaly in enumerate(self.search([]), start=1): [cite: 214]
            worksheet.write(row_num, 0, str(anomaly.date or "")) [cite: 215]
            worksheet.write(row_num, 1, anomaly.compte or "") [cite: 216]
            worksheet.write(row_num, 2, anomaly.intitule or "") [cite: 217]
            worksheet.write_number(row_num, 3, anomaly.debit or 0, workbook.add_format({'num_format': '#,##0.00'})) [cite: 218, 209]
            worksheet.write_number(row_num, 4, anomaly.credit or 0, workbook.add_format({'num_format': '#,##0.00'})) [cite: 219, 209]
            worksheet.write(row_num, 5, anomaly.type_anomalie or "") [cite: 220]

        workbook.close() [cite: 221]
        output.seek(0) [cite: 222]
        data = base64.b64encode(output.read()) [cite: 223]
        
        self.write({
            'export_file': data,
            'export_filename': 'Audit_Grand_Livre.xlsx'
        }) [cite: 224, 225, 226]

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'audit.grand.livre',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        } [cite: 228, 229, 230, 231, 232, 233]