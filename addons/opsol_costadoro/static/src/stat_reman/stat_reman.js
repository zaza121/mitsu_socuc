/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class StatREMAN extends Component {
    static template = "opsol_ajmarine.stat_reman_template";

    setup() {
        this.state = useState({ en_returned: 0 });
        this.action = useService("action");
    }

    increment() {
        this.state.en_returned++;
    }

    open_reman_encours() {
        let lview_id = this.props.statistics.list_view_id;
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "REMAN EN COURS",
            res_model: "sale.order.line",
            views: [[lview_id, "list"]],
            domain: [['reman_state', '=', 'en_cours']],
        });
    }

    open_reman_cater() {
        let lview_id = this.props.statistics.list_view_id;
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "REMAN Retourne chez Caterppillar",
            res_model: "sale.order.line",
            views: [[lview_id, "list"]],
            domain: [['reman_state', '=', 'return_cat']],
        });
    }

    open_reman_holdaj() {
        let lview_id = this.props.statistics.list_view_id;
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "REMAN Retenu chez AJMARINE",
            res_model: "sale.order.line",
            views: [[lview_id, "list"]],
            domain: [['reman_state', '=', 'hold']],
        });
    }

    open_reman_holcust() {
        let lview_id = this.props.statistics.list_view_id;
        this.action.doAction({
            type: "ir.actions.act_window",
            name: "REMAN Retenu par le Client",
            res_model: "sale.order.line",
            views: [[lview_id, "list"]],
            domain: [['reman_state', '=', 'hold_customer']],
        });
    }
}