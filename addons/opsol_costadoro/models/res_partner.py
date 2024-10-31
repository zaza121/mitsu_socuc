# -*- coding: utf-8 -*-

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _get_default_product_uom_id(self):
        def_kg = self.env.ref("uom.product_uom_kgm")
        return def_kg and def_kg.id or self.env['uom.uom'].search([], limit=1, order='id').id

    gratuite = fields.Boolean(string='Gratuité', default=False)
    frais_facturation = fields.Boolean(string='Frais de facturation', default=False)
    facturation_product_id = fields.Many2one(
        comodel_name='product.template',
        string='Frais de facturation',
    )
    facturation_amount = fields.Monetary(
        string="Frais de facturation",
        compute="_compute_facturation_amount",
        store=True,
        readonly=False,
    )
    facturer_intervention = fields.Boolean(string='Facturer intervention', default=False)
    gescom_created_date = fields.Date(string='Date de création')
    gescom_map_commercial = fields.Char(string='Lien Gescom')
    zone_id = fields.Many2one(
        comodel_name='opsol_costadoro.zone_comm',
        string='Zone Commerciale',
    )
    enseigne = fields.Text(string='Enseigne')
    date_debut = fields.Date(string='Date de debut')
    date_fin = fields.Date(string='Date de fin')
    redressement_jud = fields.Boolean(string='Redressement judiciaire ?')
    date_redr_jud = fields.Date(string='Date redressement')
    ccmx = fields.Char(string='CCMX Code comptable')
    type_cafe = fields.Many2one(
        comodel_name='product.template',
        string='Type de café',
    )
    equipment_ids = fields.One2many(
        comodel_name='equipment.details',
        inverse_name='client',
        string='Equipements',
    )
    equipments_count = fields.Integer(
        string='Number of Equipment',
        compute="_compute_equipments_count"
    )
    tier_parent_id = fields.Many2one(
        comodel_name='res.partner',
        string='Tier Parent',
    )
    estimation_qty = fields.Float(string='Quantite')
    estimation_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string='Unite',
        default=_get_default_product_uom_id
    )
    transport_product_id = fields.Many2one(
        comodel_name='product.template',
        string='Frais de transport',
    )
    transport_amount = fields.Monetary(
        string="Transport amount",
        compute="_compute_transport_amount",
        store=True,
        readonly=False,
    )
    lines_metric_ids = fields.One2many(
        comodel_name='opsol_costadoro.line_metric',
        compute="compute_quick_equipment_ids",
        string='Lignes de metrique',
    )
    ana_acc_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic Account',
    )
    jour_tournee = fields.Selection(
        string="Jour de tournée",
        selection=[
            ('lun', "Lundi"),('mar', "Mardi"), ('mer', "Mercredi"), 
            ('jeu', "Jeudi"), ('ven', "Vendredi"), ('sam', "Samedi"), ('dim', "Dimanche")],
    )
    client_sur_tel = fields.Boolean(
        string='Client sur téléphone',
        default=False
    )
    heure_ouverture_text = fields.Char(
        string='Heure d\' ouverture',
        help="Heures d'ouverture du client",
    )
    heure_ouverture = fields.Float(
        string='Heure d\' ouverture', required=False, index=True,
        help="Heure d'ouverture du client", default=8.0
    )
    heure_fermeture = fields.Float(
        string='Heure de fermeture', required=False, index=True,
        help="Heure de fermeture du client", default=8.0
    )
    do_avance_remise = fields.Boolean(
        string='Avance sur remises',
        default=False
    )
    c_amount = fields.Monetary(string="Montant")
    kg_by_sem = fields.Float(string='Kg/sem',)
    kg_total_prevu = fields.Float(string='Kg total prévu',)
    euro_by_kg = fields.Monetary(string='€/kg')
    jours_fermeture_ids = fields.Many2many(
        comodel_name='opsol_costadoro.jour_semaine',
        string='Jours de la semaine',
    )

    def compute_quick_equipment_ids(self):
        for rec in self:
            rec.lines_metric_ids = rec.equipment_ids.mapped("lines_metric_ids")

    @api.depends('transport_product_id')
    def _compute_transport_amount(self):
        for rec in self:
            rec.transport_amount = rec.transport_product_id and rec.transport_product_id.list_price or 0

    @api.depends('facturation_product_id')
    def _compute_facturation_amount(self):
        for rec in self:
            rec.facturation_amount = rec.facturation_product_id and rec.facturation_product_id.list_price or 0

    def _compute_equipments_count(self):
        for rec in self:
            rec.equipments_count = len(rec.equipment_ids)

    def action_open_equipments(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("client_equipment.action_equipment_details")
        action['domain'] = [('id', 'in', self.equipment_ids.ids)]
        action['context'] = {}
        return action

    def action_open_salelines(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("opsol_costadoro.action_soline_opsol")
        action['domain'] = [('order_partner_id', '=', self.id), ('state', '=', 'sale')]
        return action
