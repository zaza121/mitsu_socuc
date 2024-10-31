# -*- coding: utf-8 -*-

import logging
import random

from odoo import http
from odoo.http import request

logger = logging.getLogger(__name__)

class AwesomeDashboard(http.Controller):
    @http.route('/reman/statistics', type='json', auth='user')
    def get_statistics(self):
        """Return a list of the course products values with formatted price."""
        products = request.env['product.product'].search([('detailed_type', '=', 'course')])
        reman_lines = request.env['sale.order.line'].search([('display_type', '=', False),('is_reman', '=', True)])
        view_id = request.env.ref("opsol_ajmarine.view_sale_reman_tree").id

        reman_encours = len(reman_lines.filtered(lambda x: x.reman_state == 'en_cours'))
        reman_retcat = len(reman_lines.filtered(lambda x: x.reman_state == 'return_cat'))
        reman_holdaj = len(reman_lines.filtered(lambda x: x.reman_state == 'hold'))
        reman_hold_customer = len(reman_lines.filtered(lambda x: x.reman_state == 'hold_customer'))
        
        bal_amount_to_return = sum(reman_lines.mapped('bal_amount_to_return'))
        bal_amount_due = sum(reman_lines.mapped('bal_amount_due'))
        bal_ret_del = sum(reman_lines.mapped('bal_return_delay'))
        bal_cred_del = sum(reman_lines.mapped('bal_credit_delay'))

        return {
            'list_view_id': view_id,
            'en_returned': 400000,
            'r_encours': reman_encours,
            'r_retcat': reman_retcat,
            'r_holdaj': reman_holdaj,
            'r_holdcust': reman_hold_customer,
            'bal_amt_ret': bal_amount_to_return,
            'bal_amt_due': bal_amount_due,
            'bal_ret_del': bal_ret_del,
            'bal_cred_del': bal_cred_del,
        }
