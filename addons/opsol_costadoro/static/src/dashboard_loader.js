/** @odoo-module */

import { registry } from "@web/core/registry";
import { LazyComponent } from "@web/core/assets";
import { Component, xml } from "@odoo/owl";

class REMANDashboardLoader extends Component {
    static components = { LazyComponent };
    static template = xml`
    <LazyComponent bundle="'opsol_ajmarine.dashboard'" Component="'REMANDashboard'" props="props"/>
    `;

}

registry.category("actions").add("opsol_ajmarine.dashboard", REMANDashboardLoader);
