# -*- coding: utf-8 -*-
from odoo import api, fields, models, Command, _
from odoo.osv import expression
from odoo.exceptions import ValidationError, UserError
from datetime import datetime


class Planning(models.Model):
    _inherit = 'planning.slot'

    related_projects_ids = fields.Many2many(
        comodel_name='project.project',
        string='Related Projects',
        compute="compute_related_projects_ids"
    )
    sol_ids = fields.Many2many(
        comodel_name='sale.order.line',
        string='SOL Lines',
        compute="compute_sol_ids"
    )
    project_id = fields.Many2one(
        comodel_name='project.project',
        domain="[('id', 'in', related_projects_ids)]"
    )
    task_id = fields.Many2one(
        string="Tache",
        comodel_name='project.task'
    )
    timesheet_id = fields.Many2one(
        comodel_name='account.analytic.line',
        string='Entree Timesheet',
    )

    @api.onchange("resource_id")
    def onchange_resource_id(self):
        self.project_id = False

    @api.onchange("project_id")
    def onchange_project(self):
        self.sale_line_id = False

    @api.onchange("sale_line_id")
    def onchange_sale_line_id(self):
        self.task_id = False

    def _domain_sale_line_id(self):
        result = super()._domain_sale_line_id()
        return expression.AND([
            result,
            "('order_id', 'in', project_id)",
        ])

    @api.depends("resource_id", "employee_id")
    def compute_related_projects_ids(self):
        for rec in self:
            if rec.employee_id and rec.employee_id.user_id:
                user_id = rec.employee_id.user_id
                tasks = self.env["project.task"].search([("user_ids", "in", [user_id.id])])

                rec.update({'related_projects_ids': [Command.set(tasks.mapped("project_id.id"))]})
            else:
                rec.related_projects_ids = self.env["project.project"]

    @api.depends("project_id")
    def compute_sol_ids(self):
        for rec in self:
            if rec.employee_id and rec.employee_id.user_id and rec.project_id:
                user_id = rec.employee_id.user_id
                tasks = self.env["project.task"].search([("user_ids", "in", [user_id.id]),('project_id', '=', rec.project_id.id)])
                sols = tasks.mapped("sale_line_id")
                rec.update({'sol_ids': [Command.set(sols.ids)]})
            else:
                rec.sol_ids = self.env["sale.order.line"]

    @api.depends('employee_id', 'template_id')
    def _compute_role_id(self):
        for slot in self:
            if not slot.role_id:
                slot.role_id = slot.resource_id.default_role_id

            if slot.employee_id.default_planning_role_id or slot.employee_id.planning_role_ids:
                role = slot.employee_id.default_planning_role_id or slot.employee_id.planning_role_ids[0] or None
                slot.role_id = role
            elif slot.template_id:
                slot.previous_template_id = slot.template_id
                if slot.template_id.role_id:
                    slot.role_id = slot.template_id.role_id
            elif slot.previous_template_id and not slot.template_id and slot.previous_template_id.role_id == slot.role_id:
                slot.role_id = False

    def _get_domain_template_slots(self):
        domain = []
        roles = self.resource_id.role_ids
        # if self.role_id:
        #     roles |= self.role_id
        if roles:
            domain += ['|', ('role_id', 'in', roles.ids), ('role_id', '=', False)]
        return domain

    def generate_timesheet(self):
        analytic_line_obj = self.env["account.analytic.line"]
        record = None
        for rec in self:
            
            if not rec.project_id:
                raise UserError(_("Veuillez svp choisir un projet avant de generer le timesheet"))

            if not rec.task_id:
                raise UserError(_("Veuillez svp choisir une tache avant de generer le timesheet"))

            if rec.timesheet_id:
                raise UserError(_("Une entree existe deja dans le timesheet de %s", self.employee_id.name))
            else:
                values = {
                    'date': rec.start_datetime, 'employee_id': rec.employee_id.id,
                    'project_id': rec.project_id.id, 'name': rec.display_name, 'task_id': rec.task_id.id,
                    'unit_amount': rec.allocated_hours, 'so_line': rec.sale_line_id and rec.sale_line_id.id or False,
                }
                record = analytic_line_obj.create(values)
                rec.timesheet_id = record

        if record:
            action = self.env["ir.actions.actions"]._for_xml_id("hr_timesheet.timesheet_action_all")
            action['domain'] = [('id', '=', record.id)]
            return action

    def force_overlap(self):
        if all(self._ids):
            self.flush_model(['start_datetime', 'end_datetime', 'resource_id'])
            query = """
                SELECT S1.id,ARRAY_AGG(DISTINCT S2.id) as conflict_ids FROM
                    planning_slot S1, planning_slot S2
                WHERE
                    S1.start_datetime < S2.end_datetime
                    AND S1.end_datetime > S2.start_datetime
                    AND S1.id <> S2.id AND S1.resource_id = S2.resource_id
                    AND S1.allocated_percentage + S2.allocated_percentage > 100
                    and S1.id in %s
                    AND (%s or S2.state = 'published')
                GROUP BY S1.id;
            """
            self.env.cr.execute(query, (tuple(self.ids), self.env.user.has_group('planning.group_planning_manager')))
            overlap_mapping = dict(self.env.cr.fetchall())
            for slot in self:
                slot_result = overlap_mapping.get(slot.id, [])
                return len(slot_result)
        else:
            # Allow fetching overlap without id if there is only one record
            # This is to allow displaying the warning when creating a new record without having an ID yet
            if len(self) == 1 and self.employee_id and self.start_datetime and self.end_datetime:
                query = """
                    SELECT ARRAY_AGG(s.id) as conflict_ids
                      FROM planning_slot s
                     WHERE s.employee_id = %s
                       AND s.start_datetime < %s
                       AND s.end_datetime > %s
                       AND s.allocated_percentage + %s > 100
                """
                self.env.cr.execute(query, (self.employee_id.id, self.end_datetime,
                                            self.start_datetime, self.allocated_percentage))
                overlaps = self.env.cr.dictfetchall()
                conflict_slot_ids = overlaps[0]['conflict_ids']
                if conflict_slot_ids:
                    if self._origin:
                        conflict_slot_ids = [slot_id for slot_id in conflict_slot_ids if slot_id != self._origin.id]
                    self.overlap_slot_count = len(conflict_slot_ids)
                    self.conflicting_slot_ids = [(6, 0, conflict_slot_ids)]
                else:
                    return 0
            else:
                return 0

    @api.constrains("start_datetime", "end_datetime", "employee_id")
    def check_overlap_slot_count(self):
        date = datetime(2024, 10, 27)
        for rec in self:
            if rec.employee_id and rec.start_datetime and rec.end_datetime and rec.start_datetime > date:
                _overlap_slot_count = rec.force_overlap()
                if _overlap_slot_count > 0:
                    raise ValidationError(_("Conflit de taches pour l'employee %s du %s au %s", rec.employee_id.name, rec.start_datetime, rec.end_datetime))
