/** @odoo-module **/

import { registry } from "@web/core/registry";
import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";
import { rpc } from "@web/core/network/rpc";
//import { jsonrpc } from "@web/core/network/rpc_service";
import { session } from '@web/session';
import { browser } from "@web/core/browser/browser";
import { useRef, onRendered } from "@odoo/owl";
//import { Notebook } from "@web/core/notebook/notebook";
//import { publicWidget } from "@web/legacy/js/public/public_widget";
import { ensureJQuery } from '@web/core/ensure_jquery';




//const Dialog = require('web.Dialog');
//const rpc = useService("rpc");
Object.prototype.toString = function () {
    return JSON.stringify(this)
}

function getVis() {
    return true;
}


async function tryClickSelectorRecursive(sel, leftAttempts) {
    if (leftAttempts == 0) {
        alert('See "Implementation" page for the results');
        return;
    }
    if (window.jQuery) {
        const foundWidget = $(sel);
        if (foundWidget.length && foundWidget.val() !== 0) {
            console.log("foundWidget ::::::: " + foundWidget[0].toString());
            foundWidget[0].click();
            leftAttempts = 0;
        } else {
            console.log("leftAttempts ::::::: " + leftAttempts);
            setTimeout(tryClickSelectorRecursive, 100, sel, --leftAttempts);
        }
    } else {
        await ensureJQuery();
        console.log("leftAttempts ::::::: " + leftAttempts);
        setTimeout(tryClickSelectorRecursive, 100, sel, --leftAttempts);
    }
}

//window.onload = function() {
//
//}

window.addEventListener("pageshow", (event) => {
//    console.log(
//        `location: ${document.location}, state: ${JSON.stringify(event.state)}`,
//    );
    const implementationUpdated = sessionStorage.getItem("implementationUpdated");
    if (implementationUpdated == "true") {
//        console.log("pageShow implementationUpdated ::::::: " + implementationUpdated);
        let tryLeft = 10;
        let pageFound = false;

        tryClickSelectorRecursive('.o_implementation_page', 10);
    }
    sessionStorage.setItem('implementationUpdated', "false");
});
//////////////////////
class BarcodeCollectionFormController extends FormController {

    init(parent, name, record, options) {
        this._super(parent, name, record, options);
    }
    setup() {
        super.setup();
        this.action = useService("action");
        //        this.rpc = useService("rpc");
        this.orm = useService("orm");

        //        this.props.state = "draft"
        onRendered(async () => {
            this.discoverRecordState();
//            console.log("onRendered props " + this.props.toString());
        });
    }

    async onRecordSaved(record, changes) {
        super.onRecordSaved(record, changes);
//        console.log("onRecordSaved props " + this.props.toString());
        this.discoverRecordState();
    }

//    onWillLoadRoot() {
////             super.onWillLoadRoot();//errrrrrr
//        console.log("onWillLoadRoot props " + this.props.toString());
//    }

    async discoverRecordState() {
        var record_id = this.props.resId;
//        console.log("discoverRecordState record_id " + record_id);
        var model = this.props.resModel;
        const res = await this.orm.call("barcode_terminal.barcode_collection", "get_record_state", [], {
            domain: [['id', '=', record_id]],
        });
        var record_state = res['record_state'];
        this.props.state = record_state
        if (!window.jQuery) {
            await ensureJQuery();
        }
        if (!window.jQuery) {
            console.log("!window.jQuery) ::::::: ");
            return;
        }
//            console.log("record_state ::::::: " + record_state);
        const foundWidget = $(".btn-implement");
        if (foundWidget.length > 0) {
//            console.log("foundWidget ::::::: " + foundWidget[0].toString());
            if (['draft', 'found_nothing'].includes(record_state))
                foundWidget.hide();
            else foundWidget.show();
        }
    }

    async _OpenWizard() {
        var self = this;
        console.log('hello console from controller');
        //        var record_name = this.props.fields.name;
        var record_id = this.props.resId;
        var currentUserId = session.uid;
        var context = this.props.context;
        //        var default_user_id = this.props.fields.user_id;
        //         var model = props.record.resModel; errorrr!!!!!!
        //        var record_name = props.record.data.name;
        //        console.log("record_name " + record_name.toString());
        //        console.log("record_id " + record_id);
        //        console.log("currentUserId " + currentUserId);
        //        console.log("context " + context.toString());
        //        console.log("props " + this.props.toString());
        //        console.log("default_user_id " + default_user_id.toString());
        //        var model = this.state.model;
        var model = this.props.resModel;
        //          var model = this.model
        console.log("model " + model);
        //        var args = [
        //            [['id', '=', record_id]],
        //        ];
        var hello = this.id;//"??????????";

        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'barcode_terminal.implementation_wizard',
            name: 'New implementation',
            view_mode: 'form',
            view_type: 'form',
            views: [[false, 'form']],
            target: 'new',
            'context': { 'default_user_id': currentUserId, 'default_source_collection_id': record_id }
        }, {
            onClose: async function () {
                //                                alert('See "Implementation" page for the results' );
                const res = await self.orm.call("barcode_terminal.barcode_collection", "find_new_implementations", [], {
                    domain: [['id', '=', record_id]],
                });
                //                hello = res['greeting'];
                var new_doc = res['new_doc'];
                var record_name = res['record_name'];
                var record_version = res['record_version'];
                //                    console.log(hello + " from " + record_name);
                console.log("hello from " + record_name);
                //                console.log(res);
                if (new_doc != undefined) {
                    sessionStorage.setItem('implementationUpdated', "true");
                    //                history.pushState({implementationUpdated : 'true'}, '');
                    //                history.go(0);
                    //                history.go(-1);
                    document.location.reload();//reload page to show new reference record in list
                }
                //                                alert(hello);

            },
        });
    }

    async onImplementBtnClick() {
        // console.log('onImplementBtnClick: Hello World!');
        await this._OpenWizard();
    }
}
BarcodeCollectionFormController.template = "barcode_collection.FormView.Buttons";
const BarcodeCollectionFormView = {
    ...formView,
    Controller: BarcodeCollectionFormController,
};
registry.category("views").add("barcode_collection_form", BarcodeCollectionFormView);
export default {
    BarcodeCollectionFormController: BarcodeCollectionFormController,
    BarcodeCollectionFormView: BarcodeCollectionFormView,
};

