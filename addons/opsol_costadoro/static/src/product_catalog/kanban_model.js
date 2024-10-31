/** @odoo-module */
import { ProductCatalogKanbanModel } from "@product/product_catalog/kanban_model";
import { patch } from "@web/core/utils/patch";
import { useSubEnv } from "@odoo/owl";

patch(ProductCatalogKanbanModel.prototype, {
    _get_extra_context(params){
        return {extra_context: params.context};
    },
    async _loadData(params) {
        const result = await super._loadData(...arguments);
        if (!params.isMonoRecord && !params.groupBy.length) {
            const orderLinesInfo = await this.rpc("/product/catalog/order_lines_info", Object.assign({
                order_id: params.context.order_id,
                product_ids: result.records.map((rec) => rec.id),
                res_model: params.context.product_catalog_order_model,
            }, this._get_extra_context(params || {})));
            for (const record of result.records) {
                record.productCatalogData = orderLinesInfo[record.id];
            }
        }
        return result;
    }
});
