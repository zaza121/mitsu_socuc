# -*- coding: utf-8 -*-
from odoo import api, fields, models
class JsaQuestions(models.Model):
    _name = "jsa.questions"
    _description = "Jsa Questions"

    name = fields.Char('Reference')
    stage = fields.Selection([('pre', 'Pre-Works'), ('post', 'Post-Works')], string="Stage", default='post')
    active = fields.Boolean(default=True)
    question = fields.Char('Question')

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('jsa.questions')
        return super(JsaQuestions, self).create(vals)
