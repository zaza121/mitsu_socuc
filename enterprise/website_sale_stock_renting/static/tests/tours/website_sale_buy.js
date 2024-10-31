/** @odoo-module **/

import { registry } from "@web/core/registry";
import * as tourUtils from '@website_sale/js/tours/tour_utils';

registry.category("web_tour.tours").add('shop_buy_rental_stock_product', {
    url: '/shop',
    steps: () => [
        {
            content: "Search computer write text",
            trigger: 'form input[name="search"]',
            run: "edit computer",
        },
        {
            content: "Search computer click",
            trigger: 'form:has(input[name="search"]) .oe_search_button',
            run: "click",
        },
        {
            content: "Select computer",
            trigger: '.oe_product_cart:first a:contains("Computer")',
            run: "click",
        },
        {
            content: "Check if the default data is in the date picker input",
            trigger: '.o_daterange_picker[data-has-default-dates=true]',
        },
        {
            content: "Open daterangepicker",
            trigger: 'input[name=renting_start_date]',
            run: "click",
        },
        { // ensures only one day is selected
            content:  "Select Date field",
            trigger:  ".o_date_picker .o_highlight_end",
            run: "click",
        },
        {
            content: "Pick start time",
            trigger: '.o_time_picker_select:eq(0)',
            run: "select 8",
        },
        {
            content: "Pick end time",
            trigger: '.o_time_picker_select:eq(2)',
            run: "select 12",
        },
        {
            content: "Apply change",
            trigger: '.o_datetime_buttons button.o_apply',
            run: "click",
        },
        {
            content: "Add one quantity",
            trigger: '.css_quantity a.js_add_cart_json i.fa-plus',
            run: "click",
        },
        {
            content: "click on add to cart",
            trigger: '#product_detail form[action^="/shop/cart/update"] #add_to_cart',
            run: "click",
        },
        tourUtils.goToCart({quantity: 2}),
        {
            content: "Verify there is a Computer",
            trigger: '#cart_products div a h6:contains("Computer")',
        },
        {
            content: "Verify there are 2 quantity of Computers",
            trigger: '#cart_products div div.css_quantity input[value="2"]',
        },
        {
            content: "Go back on the Computer",
            trigger: '#cart_products div>a>h6:contains("Computer")',
            run: "click",
        },
        {
            content: "Verify there is a warning message",
            trigger: 'div#threshold_message_renting:contains("Only 3 Units still available during the selected period.")',
        },
        tourUtils.goToCart({quantity: 2}),
        {
            content: "Check quantity",
            trigger: '#cart_products input.js_quantity:value(2)',
        },
        {
            content: "Check amount",
            trigger: '#cart_products .oe_currency_value:contains(28.00)',
        },
        tourUtils.goToCheckout(),
        tourUtils.confirmOrder(),
        ...tourUtils.payWithTransfer(true),
    ]
});
