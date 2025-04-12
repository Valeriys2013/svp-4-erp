/** @odoo-module **/

import { formView } from '@web/views/form/form_view';
import { registry } from "@web/core/registry";
import { BarcodeCollectionFormRenderer } from '@barcode_terminal/js/formrenderer';
//console.log('SaleOrderRender',BarcodeCollectionFormRenderer)
export const BarcodeCollectionFormView = {
   ...formView,
   Renderer: BarcodeCollectionFormRenderer,
};
registry.category("views").add("barcode_collection_form", BarcodeCollectionFormView);

//const actionHandlersRegistry = registry.category("action_handlers");
//actionHandlersRegistry.add("ir.action_in_handler_registry", ({ action }) =>{
////            assert.step(action.type);
////alert('This is called from action_in_handler_registry');
////            console.log( 'Hello World' );
//}
//);