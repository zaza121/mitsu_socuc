# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from . import base_geocoder

class EquipmentDetails(models.Model):
    _name = "equipment.details"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Equipment Details"

    name = fields.Char('Equipment Name', required=True, translate=True)
    category_id = fields.Many2one('equipment.category', string='Equipment Category',
                                  tracking=True, group_expand='_read_group_category_ids')
    client = fields.Many2one('res.partner', string='Client', tracking=True)
    manufacturer_id = fields.Many2one('equipment.manufacturer', string='Manufacturer')
    ref = fields.Char('Reference')
    location = fields.Char('Equipment Location')
    address = fields.Char('Equipment Address')
    model = fields.Char('Model')
    serial_no = fields.Char('Serial Number', copy=False, required=True)
    image = fields.Image(string="Image")
    street = fields.Char('Street')
    street2 = fields.Char('Street2')
    zip = fields.Char('Zip')
    city = fields.Char('City')
    state = fields.Many2one("res.country.state", string='State')
    country = fields.Many2one('res.country', string='Country')
    site_contact = fields.Char(string="Site Contact")
    site_phone = fields.Char(string="Site Phone")

    note = fields.Html(string='Note')
    history = fields.Html('History')

    latitude = fields.Float('Latitude', digits=(10, 7))
    longitude = fields.Float('Longitude', digits=(10, 7))
    file_ids = fields.Many2many('ir.attachment', string="Documents", copy=False)
    jobs = fields.One2many('equipment.jobs', 'equipment', string='Jobs')


    # @api.model
    # def geo_localize(self, street='', zip='', city='', state='', country=''):
    #     geo_obj = self.env['base.geocoder']
    #     search = geo_obj.geo_query_address(street=street, zip=zip, city=city, state=state, country=country)
    #     result = geo_obj.geo_find(search, force_country=country)
    #     if result is None:
    #         search = geo_obj.geo_query_address(city=city, state=state, country=country)
    #         result = geo_obj.geo_find(search, force_country=country)
    #     return result

    @api.onchange('client')
    def onchange_client(self):
        self.site_contact = self.client.site_contact
        self.site_phone = self.client.site_phone

    @api.model
    def create(self, vals):
        vals['site_contact'] = self.env['res.partner'].search([('id', '=', vals['client'])]).site_contact
        vals['site_phone'] = self.env['res.partner'].search([('id', '=', vals['client'])]).site_phone
        res = super(EquipmentDetails, self).create(vals)
        return res

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        if default is None:
            default = {}
        if not default.get('name'):
            default['name'] = _("%s (copy)", self.name)
            return super(EquipmentDetails, self).copy(default)

    _sql_constraints = [
        ('unique_equipment_serial_no', 'unique (serial_no)', 'Serial No must be unique.')
    ]

class EquipmentCategory(models.Model):
    _name = "equipment.category"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "equipment.category"

    name = fields.Char('Category Name', required=True, translate=True)

class EquipmentManufacturer(models.Model):
    _name = "equipment.manufacturer"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "equipment.manufacturer"

    name = fields.Char('Manufacturer Name', required=True, translate=True)




