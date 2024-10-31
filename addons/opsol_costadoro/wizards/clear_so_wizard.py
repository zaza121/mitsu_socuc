from odoo import fields, models

LABEL_RUBRIQUE = {
    'all': 'Clean all',
    'mepa': 'ME Parts',
    'meot': 'ME Others',
    'gspa': 'GS Parts',
    'gsot': 'GS Others',
    'gbpa': 'GB Parts',
    'gbot': 'GB Others',
    'gsadpa': 'Supply Parts',
    'gsadot': 'GS AD Others',
}


class ClearSoWizard(models.TransientModel):
    _inherit = "clear.order.lines.so"

    rubrique = fields.Selection(
        selection=list(LABEL_RUBRIQUE.items()),
        string="Rubrique",
        default="mepa",
        required=True
    )

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

    def get_default_item_value(self):
        return {'rubrique': self.rubrique}

    def clear_order_lines_so(self):
        self.ensure_one()
        records = self.env['sale.order'].browse(self._context.get('active_ids', []))
        if records:
            target = self.rubrique and self.get_target_field() or 'order_line'
            records.mapped(target).unlink()

            msg_body = f"Has cleared order lines of {self.rubrique}"
            records.message_post(body=msg_body, message_type='notification')
