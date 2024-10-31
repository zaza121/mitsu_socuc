# -*- coding: utf-8 -*-
from odoo import api, fields, models


class EquipmentJobs(models.Model):
    _inherit = 'equipment.jobs'

    task_id = fields.Many2one(
        string='Task',
        comodel_name="project.task"
    )
    location = fields.Char(
        compute="compute_equipment_info",
        store=True,
        readonly=False
    )
    model = fields.Char(
        compute="compute_equipment_info",
        store=True,
        readonly=False
    )
    serial_no = fields.Char(
        compute="compute_equipment_info",
        store=True,
        readonly=False
    )
    street = fields.Char(
        compute="compute_equipment_info",
        store=True,
        readonly=False
    )
    street2 = fields.Char(
        compute="compute_equipment_info",
        store=True,
        readonly=False
    )
    zip = fields.Char(
        compute="compute_equipment_info",
        store=True,
        readonly=False
    )
    city = fields.Char(
        compute="compute_equipment_info",
        store=True,
        readonly=False
    )
    state = fields.Many2one(
        comodel_name="res.country.state", 
        compute="compute_equipment_info",
        store=True,
        readonly=False
    )
    country = fields.Many2one(
        comodel_name='res.country', 
        compute="compute_equipment_info",
        store=True,
        readonly=False
    )
    note = fields.Html(
        compute="compute_equipment_info",
        store=True,
        readonly=False
    )

    @api.depends('equipment')
    def compute_equipment_info(self):
        for rec in self:
            rec.location = rec.equipment.location
            rec.serial_no = rec.equipment.serial_no
            rec.model = rec.equipment.model
            rec.street = rec.equipment.street
            rec.street2 = rec.equipment.street2
            rec.zip = rec.equipment.zip
            rec.city = rec.equipment.city
            rec.state = rec.equipment.state
            rec.country = rec.equipment.country
            rec.note = rec.equipment.note

    @api.onchange('serial_no')
    def onchange_serial_no(self):
        for row in self:
            row.equipment = self.env['equipment.details'].search([('serial_no', '=', row.serial_no)]).id
