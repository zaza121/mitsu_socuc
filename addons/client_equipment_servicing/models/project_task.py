
from odoo import api, models, fields

class ProjectTask(models.Model):
    _inherit = "project.task"

    site_contact = fields.Char(string="Site Contact")
    site_phone = fields.Char(string="Site Phone")
    equipment_ids = fields.One2many('equipment.jobs', inverse_name='task_id', string='Job', tracking=True)
    supervisor = fields.Many2one('hr.employee', string='Site Supervisor', tracking=True)
    signature = fields.Binary(string='Supervisor Signature')
    pre_responses_ids = fields.One2many('jsa_pre.responses', 'task_id')
    post_responses_ids = fields.One2many('jsa_post.responses', 'task_id')
    project_name = fields.Char(string="Project Name", compute="_compute_project_name")
    load = fields.Boolean(string='Load')

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        self.site_contact = self.partner_id.site_contact
        self.site_phone = self.partner_id.site_phone

    @api.model
    def create(self, vals):
        if 'project_name' in vals:
            if vals['project_name'] != "Field Service":
                vals['load'] = True
        vals['site_contact'] = self.env['res.partner'].search([('id', '=', vals['partner_id'])]).site_contact
        vals['site_phone'] = self.env['res.partner'].search([('id', '=', vals['partner_id'])]).site_phone
        print(vals)
        res = super(ProjectTask, self).create(vals)
        return res

    def action_load_jsa(self):
        self.load = True
        if len(self.pre_responses_ids) == 0:
            pre_question_ids = self.env['jsa.questions'].search([('active', '=', 'true'), ('stage','=', 'pre')])
            post_question_ids = self.env['jsa.questions'].search([('active', '=', 'true'), ('stage','=', 'post')])
            for quest in pre_question_ids:
                print("pre test.111", quest.stage)
                question = {
                    'name': quest.name,
                    'question': quest.question,
                    'task_id': self.id
                }
                self.pre_responses_ids.create(question)
            for quest in post_question_ids:
                question = {
                    'name': quest.name,
                    'question': quest.question,
                    'task_id': self.id
                }
                self.post_responses_ids.create(question)

    def _compute_project_name(self):
        self.project_name = self.project_id.name



