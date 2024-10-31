/** @odoo-module */
import { ProductCatalogKanbanRecord } from "@product/product_catalog/kanban_record";
import { patch } from "@web/core/utils/patch";
import { useSubEnv } from "@odoo/owl";

patch(ProductCatalogKanbanRecord.prototype, {
    setup() {
        super.setup();
        useSubEnv({
            aj_rub: this.props.record.context.aj_rub,
        });
    },
    _get_extra_context(){
        return {aj_rub: this.env.aj_rub};
    },
    _updateQuantityAndGetPrice() {
        return this.rpc("/product/catalog/update_order_line_info", Object.assign({
            order_id: this.env.orderId,
            product_id: this.env.productId,
            quantity: this.productCatalogData.quantity,
            res_model: this.env.orderResModel,
        }, this._get_extra_context()));
    }
});
