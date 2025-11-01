import logging
import requests
from datetime import datetime, timedelta, timezone
from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------------
# CALENDAR EVENT AND APPOINTMENT TYPE (Existing Logic Retained)
# ----------------------------------------------------------------------------

class AppointmentType(models.Model):
    _inherit = 'appointment.type'

    teams_enabled = fields.Boolean(string="Activer Teams (Post-Paiement)", help="Créer automatiquement une réunion Teams pour ce type de rendez-vous APRÈS la validation du paiement de la facture.")


class CalendarEventTeams(models.Model):
    _inherit = 'calendar.event'  

    teams_meeting_url = fields.Char(string="Lien Teams", readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        # SUPPRESSION de l'appel à _create_teams_meeting ici. 
        # Le trigger est déplacé à la validation du paiement de la facture.
        return records

    def _get_oauth_token(self):
        IrConfig = self.env['ir.config_parameter'].sudo()
        tenant = IrConfig.get_param('appointment_teams_auto.tenant_id')
        client_id = IrConfig.get_param('appointment_teams_auto.client_id')
        client_secret = IrConfig.get_param('appointment_teams_auto.client_secret')

        if not all([tenant, client_id, client_secret]):
            raise UserError(_("Les paramètres Azure (tenant, client ID, client secret) ne sont pas configurés."))

        token = IrConfig.get_param('appointment_teams_auto.token')
        expiry_str = IrConfig.get_param('appointment_teams_auto.token_expiry')
        
        # Vérification du cache du token
        if token and expiry_str:
            try:
                expiry = datetime.fromisoformat(expiry_str)  
                if expiry > datetime.utcnow().replace(tzinfo=timezone.utc) + timedelta(seconds=30):
                    return token
            except Exception:
                pass

        url_token = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
        data = {
            'grant_type': 'client_credentials',
            'client_id': client_id,
            'client_secret': client_secret,
            'scope': 'https://graph.microsoft.com/.default',
        }
        resp = requests.post(url_token, data=data, timeout=20)
        
        if resp.status_code != 200:
            _logger.error("Erreur token OAuth: %s %s", resp.status_code, resp.text)
            raise UserError(_("Impossible d'obtenir le token OAuth depuis Microsoft: %s") % resp.text)

        j = resp.json()
        access_token = j.get('access_token')
        expires_in = j.get('expires_in', 3600)
        
        if not access_token:
            raise UserError(_("Réponse token invalide: %s") % j)

        expiry = datetime.utcnow().replace(tzinfo=timezone.utc) + timedelta(seconds=int(expires_in))
        IrConfig.set_param('appointment_teams_auto.token', access_token)
        IrConfig.set_param('appointment_teams_auto.token_expiry', expiry.isoformat())
        return access_token

    def _create_teams_meeting(self, booking):
        IrConfig = self.env['ir.config_parameter'].sudo()
        user_email = IrConfig.get_param('appointment_teams_auto.account_email')

        if not user_email:
            raise UserError(_("Le compte (teams_account_email) n'est pas configuré dans les paramètres."))

        token = self._get_oauth_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        # Conversion des dates au format ISO UTC (YYYY-MM-DDTHH:MM:SSZ)
        def to_iso_z(dt):
            if not dt:
                return None
            
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
                
            return dt.isoformat().replace('+00:00', 'Z')

        start_iso = to_iso_z(booking.start)
        end_iso = to_iso_z(booking.stop)

        if not start_iso or not end_iso:
            raise UserError(_("Dates de rendez-vous non valides pour l'API Teams."))

        payload = {
            "subject": f"Rendez-vous Odoo : {booking.name or booking.appointment_type_id.name or 'Rendez-vous'}",
            "startDateTime": start_iso,
            "endDateTime": end_iso
        }

        url = f"https://graph.microsoft.com/v1.0/users/{user_email}/onlineMeetings"
        resp = requests.post(url, headers=headers, json=payload, timeout=20)

        if resp.status_code not in (200, 201):
            _logger.error("Erreur création onlineMeeting: %s %s", resp.status_code, resp.text)
            raise UserError(_("Erreur création réunion Teams: %s") % resp.text)

        return resp.json()

    def action_open_teams_link(self):
        self.ensure_one()
        if not self.teams_meeting_url:
            raise UserError(_("Aucun lien Teams disponible pour ce rendez-vous."))
        return {
            'type': 'ir.actions.act_url',
            'url': self.teams_meeting_url,
            'target': 'new',
        }


# ----------------------------------------------------------------------------
# ACCOUNT MOVE (NEW TRIGGER LOGIC)
# ----------------------------------------------------------------------------

class AccountMove(models.Model):
    _inherit = 'account.move'

    teams_link_created = fields.Boolean(string="Lien Teams Créé", copy=False, default=False)

    def _get_appointment_event(self):
        """
        Tente de trouver l'événement de calendrier lié à cette facture.
        """
        self.ensure_one()
        
        # 1. Trouver les lignes de vente à partir des lignes de facture
        sale_lines = self.invoice_line_ids.mapped('sale_line_ids')
        sale_orders = sale_lines.mapped('order_id')
        
        # 2. Trouver l'événement de calendrier à partir des commandes de vente.
        event = self.env['calendar.event']
        for so in sale_orders:
            # Vérifier si l'événement est lié au SO via le champ patché ou existant
            if 'appointment_event_id' in so._fields and so.appointment_event_id:
                event = so.appointment_event_id
                break
        
        # 3. Vérifier la configuration Teams
        if event and event.appointment_type_id.teams_enabled:
            return event
            
        return self.env['calendar.event'] // recordset vide si non trouvé/non activé

    def _create_teams_meeting_if_paid(self):
        """ Déclenche la création du lien Teams si la facture est payée et que le lien n'a pas encore été créé. """
        
        // On filtre sur les factures postées et entièrement payées, mais pas encore traitées pour Teams
        for move in self.filtered(lambda m: m.state == 'posted' and m.payment_state in ('paid', 'in_payment') and not m.teams_link_created):
            
            event = move._get_appointment_event()
            
            if event:
                try:
                    # Crée la réunion Teams via la méthode de l'événement de calendrier
                    meeting = event._create_teams_meeting(event) 
                    
                    if meeting:
                        join_url = meeting.get('joinWebUrl') or meeting.get('joinUrl')
                        
                        if join_url:
                            # 1. Mise à jour de l'événement et ajout du lien dans la description
                            event.write({
                                'teams_meeting_url': join_url,
                                'description': (event.description or '') + f'\n\nLien Microsoft Teams: {join_url}',
                            })
                            # 2. Marquer la facture comme traitée pour éviter les doubles créations
                            move.teams_link_created = True
                            
                            _logger.info("Teams meeting créé par paiement facture %s pour event %s : %s", move.id, event.id, join_url)
                            
                            # 3. Envoi de l'e-mail au client (Respect de l'étape 3 du flux)
                            template = self.env.ref('calendar_appointment.calendar_event_template_meeting_invitation', raise_if_not_found=False)
                            if template:
                                # L'envoi se fait en mode sudo pour assurer les droits
                                with self.env.sudo():
                                    template.send_mail(event.id, force_send=True)
                                
                except Exception as e:
                    _logger.exception("Erreur lors de la création de la réunion Teams via la facture %s: %s", move.id, e)

    def write(self, vals):
        // Override pour intercepter les changements de statut de paiement/validation
        res = super().write(vals)
        
        # On exécute la fonction de création Teams après la mise à jour si l'état a pu changer
        if 'payment_state' in vals or 'state' in vals:
            self._create_teams_meeting_if_paid()
            
        return res

# ----------------------------------------------------------------------------
# SALE ORDER (Helper for linkage) - MONKEY PATCH
# ----------------------------------------------------------------------------

# Ce patch simule le lien nécessaire entre la Commande de Vente et l'Événement de Calendrier
from odoo.addons.sale.models.sale_order import SaleOrder
if 'appointment_event_id' not in SaleOrder._fields:
    SaleOrder.appointment_event_id = fields.Many2one(
        'calendar.event', 
        string="Événement de Rendez-vous", 
        copy=False,
        help="Lien vers l'événement de calendrier qui a généré cette commande de vente."
    )
    
# ----------------------------------------------------------------------------
# TEAMS ADMIN HELPER (Unchanged)
# ----------------------------------------------------------------------------

class TeamsAdminHelper(models.Model):
    _name = 'appointment.teams.admin'
    _description = 'Helper pour actions admin Teams via Graph (création user, etc.)'

    @api.model
    def create_service_user(self, display_name, mail_nickname, password):
        IrConfig = self.env['ir.config_parameter'].sudo()
        token = self.env['calendar.event']._get_oauth_token()  

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }

        primary_domain = IrConfig.get_param('appointment_teams_auto.azure_primary_domain') or 'yourdomain.onmicrosoft.com'

        user_payload = {
            "accountEnabled": True,
            "displayName": display_name,
            "mailNickname": mail_nickname,
            "userPrincipalName": f"{mail_nickname}@{primary_domain}",
            "passwordProfile": {
                "forceChangePasswordNextSignIn": False,
                "password": password
            }
        }

        url = "https://graph.microsoft.com/v1.0/users"
        resp = requests.post(url, headers=headers, json=user_payload, timeout=20)
        if resp.status_code not in (200,201):
            _logger.error("Erreur création user Azure: %s %s", resp.status_code, resp.text)
            raise UserError(_("Erreur création user Azure AD: %s") % resp.text)
        return resp.json()
