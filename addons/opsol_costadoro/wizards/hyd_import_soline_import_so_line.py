import logging

from odoo import _, api, fields, models, Command
# from odoo.addons.opsol_ajmarine.models.sale_order import LABEL_RUBRIQUE

LABEL_RUBRIQUE = {
    'mepa': 'ME Parts',
    'gspa': 'GS Parts',
    'gbpa': 'GB Parts',
    'gsadpa': 'Supply Parts'}


class ImportSoLine(models.TransientModel):
    _inherit = "hyd_import_soline.import_so_line_wiz"

    rubrique = fields.Selection(
        selection=list(LABEL_RUBRIQUE.items()),
        string="Rubrique",
        default="mepa",
        required=True)

    @api.onchange('sale_order_id', 'rubrique')
    def _onchange_sale_order_id(self):
        active_model = self.env.context.get('active_model', "")
        self.res_model_id = self.env["ir.model"].search([('model', '=', active_model)], limit=1)
        related_field = self.env["ir.model.fields"].search(
            [('name', '=', self.get_target_field()),('model_id', '=', self.res_model_id.id)],
            limit=1
        )
        self.field_insertion_id = related_field or None

    def get_target_field(self):
        if self.rubrique == 'mepa':
            return 'mepa_lines_ids'
        elif self.rubrique == 'meot':
            return 'meot_lines_ids'
        elif self.rubrique == 'gspa':
            return 'gspa_lines_ids'
        elif self.rubrique == 'gsot':
            return 'gsot_lines_ids'
        elif self.rubrique == 'gbpa':
            return 'gbpa_lines_ids'
        elif self.rubrique == 'gbot':
            return 'gbot_lines_ids'
        elif self.rubrique == 'gsadpa':
            return 'gsadpa_lines_ids'
        elif self.rubrique == 'gsadot':
            return 'gsadot_lines_ids'
        else:
            return 'order_line'

    def get_dict_map(self):
        result = super().get_dict_map()
        result.update({
            'In Store': ('in_store', 'selection'),
            'Note': ('aj_note', 'char')
        })
        return result

    def get_default_item_value(self):
        return {'rubrique': self.rubrique}
