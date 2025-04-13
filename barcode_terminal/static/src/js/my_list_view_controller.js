/** @odoo-module **/
import { ListController } from "@web/views/list/list_controller";
//     import ListController from 'web.ListController';
import { listView } from '@web/views/list/list_view';
//    import ListView from 'web.Listview';
import { registry } from '@web/core/registry';
//    import viewRegistry from 'web.view_registry';
import { useService } from "@web/core/utils/hooks";
import {Dialog} from "@web/core/dialog/dialog";
//import Dialog from "@web/legacy/js/core/dialog";
//const Dialog = require('web.Dialog');
import { onMounted, onWillUnmount } from "@odoo/owl";

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export class MyListController extends ListController {
    reloadIntervalId;
    prev_id = -1;
    is_collection_tree = false;

    async reloadIfNeed() {
        const res = await this.orm.call("barcode_terminal.barcode_collection", "find_newest_collection", [],);
        var latest_id = res['latest_id'];
//        if (this.prev_id != latest_id) {
        if (this.prev_id != -1 && this.prev_id != latest_id) {
//        this.prev_id = latest_id;
            //            console.log("reload latest_id : " + latest_id)
            document.location.reload();//reload page to show new reference record in list
        }
        this.prev_id = latest_id;
        console.log("prev_id : " + this.prev_id)
    }

    setup() {
        super.setup();
        this.action = useService("action");
        this.orm = useService('orm')

        var model = this.props.resModel;
        if (model == "barcode_terminal.barcode_collection") {
            this.is_collection_tree = true;
        }
        //    console.log("is_collection_tree : " + this.is_collection_tree)
        //        onMounted(() => {
        //        })

        this.reloadIntervalId = setInterval(() => {
            if (this.is_collection_tree) {
                this.reloadIfNeed();
            }

        }, 30000);

        onWillUnmount(() => {
            clearInterval(this.reloadIntervalId);
        });

    }

    UploadZip() {
        type: 'ir.actions.act_window',
            this.actionService.doAction({
                type: 'ir.actions.act_window',
                res_model: 'barcode_terminal.import_zip_dialog',
                name: 'Import SVP Barcode Collector data',
                view_mode: 'form',
                view_type: 'form',
                views: [[false, 'form']],
                target: 'new',
                res_id: false,
            })
    }

    OpenWizard() {
        //                   console.log('SaleOrderRender')
        //        alert('export class MyListController extends ListController ');
        const { context, resModel } = this.env.searchModel;
        this.action.doAction({
            type: "ir.actions.client",
            tag: "import",
            params: { model: resModel, context },
        });

    }
    OpenTemplateWizard() {
        //                   console.log('SaleOrderRender')
        //        alert('export class MyListController extends ListController ');
var timestamp = Date.now().toString();
var self = this;
        //         type: 'ir.actions.act_window',
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            res_model: 'barcode_terminal.implementation_template_wizard',
            name: 'Generate new implementation template',
            view_mode: 'form',
            view_type: 'form',
            views: [[false, 'form']],
            target: 'new',
            res_id: false,
            context: {'timestamp': timestamp,},
        }, {
            onClose: async function () {


            const res = await self.orm.call("barcode_terminal.implementation_field_mapping", "find_new_template", [], {
                    'timestamp': timestamp,
                });
                if(res['records_cnt'] > 0){
                document.location.reload();//reload page to show new reference record in list
                }


//            sleep(500).then(() => {document.location.reload();});//due to some bug - without delay button "Discard" does not work
                //                console.log(hello);
            },
        })
    }

}
registry.category("views").add("list_plus_js_actions", {
    ...listView,
    Controller: MyListController,
    buttonTemplate: "barcode_terminal.ListView.Buttons",
});

registry.category("views").add("implementation_templates_list_plus_js_actions", {
    ...listView,
    Controller: MyListController,
    buttonTemplate: "barcode_terminal.implementation_field_mapping.ListView.Buttons",
});
