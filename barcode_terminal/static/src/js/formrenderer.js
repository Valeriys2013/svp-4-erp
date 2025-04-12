/** @odoo-module **/
import { FormRenderer } from "@web/views/form/form_renderer";
import { useService } from "@web/core/utils/hooks";
const Dialog = require('web.Dialog');
var rpc = require('web.rpc');


function tryClickSelectorRecursive(sel, leftAttempts) {
    if (leftAttempts == 0) {
        alert('See "Implementation" page for the results');
        return;
    }
    const foundWidget = $(sel);
    if (foundWidget.length && foundWidget.val() !== 0) {
        console.log("foundWidget ::::::: " + foundWidget[0].toString());
        foundWidget[0].click();
        leftAttempts = 0;
    } else {
        console.log("leftAttempts ::::::: " + leftAttempts);
        setTimeout(tryClickSelectorRecursive, 100, sel, --leftAttempts);
    }
}

window.addEventListener("pageshow", (event) => {
    console.log(
        `location: ${document.location}, state: ${JSON.stringify(event.state)}`,
    );
    const implementationUpdated = sessionStorage.getItem("implementationUpdated");
    if (implementationUpdated == "true") {
        console.log("pageShow implementationUpdated ::::::: " + implementationUpdated);
        let tryLeft = 10;
        let pageFound = false;

        //        setTimeout(function () {
        //            const translation_page = $('.o_implementation_page');
        //            if (translation_page.length) {
        //                if (translation_page.val() !== 0) {
        //                    console.log("translation_page ::::::: " + translation_page[0].toString());
        //                    translation_page[0].click();
        //                    //                    tryLeft = 0;
        //                    //                    pageFound = true;
        //                }
        //            } else {
        //                alert('See "Translation" page for the results');
        //            }
        //        }, 1000);

        tryClickSelectorRecursive('.o_implementation_page', 10);

    }
    sessionStorage.setItem('implementationUpdated', "false");
});
//////////////////////

export class BarcodeCollectionFormRenderer extends FormRenderer {

    init(parent, name, record, options) {
        this._super(parent, name, record, options);
    }

    setup() {
        var self = this;
        //        var id = this.id;
        super.setup();
        //        this.action = env.services.action;;
        this.action = useService("action");
        this.orm = useService("orm");
    }

//    on_close_fun() {
//        alert('This is called on_close_fun');
//    }
    _OpenWizard() {
        //            var self = this;
        console.log('hello consoleeeeeeee!!!!!!');

        var model = this.props.record.resModel;
        var record_name = this.props.record.data.name;
        var record_id = this.props.record.data.id;
        var default_user_id = this.props.record.data.user_id;

        console.log("model " + model);
        console.log("record_name " + record_name);
        console.log("record_id " + record_id);
        var args = [
            [['id', '=', record_id]],
        ];

        //errrr
        //        const result =  this.orm.call(this.props.record.resModel, 'model_fun_for_rpc', [this.props.record.resId]);
        //        var record_version = result['record_version'];
        //        console.log("call for method on record_version" + record_version);

        var hello = this.id;//"??????????";
        this.action.doAction({
            'type': 'ir.actions.act_window',
            'name': 'New implementation',
            'res_model': 'barcode_terminal.implementation_wizard',
            'target': 'new',
            'view_mode': 'form',
            'view_type': 'form',
            views: [[false, 'form']],
            'context': { 'default_user_id': default_user_id, 'default_source_collection_id': record_id }
        }, {
            onClose: function () {
                rpc.query({
                    model: 'barcode_terminal.barcode_collection',
                    method: 'find_new_implementations',
                    //                    method: 'model_fun_for_rpc',
                    args: args,
                }).then(function (res) {
                    //                    hello = res['greeting'];
                    var new_doc = res['new_doc'];
                    var collection = res['record_name'];
                    //                    var record_version = res['record_version'];
                    //                    alert('hello from ' + collection);
                    //                    console.log(hello + " from " + record_name);
                    console.log("new_doc " + new_doc);
                    if (new_doc != undefined) {
                        sessionStorage.setItem('implementationUpdated', "true");
                        //                history.pushState({implementationUpdated : 'true'}, '');
                        //                history.go(0);
                        //                history.go(-1);
                        document.location.reload();//reload page to show new reference record in list
                    }
                    //                alert(hello);
                });
                console.log(hello);
            },
        });
    }


    onImplementBtnClick() {
        //                const { context, resModel } = this.env.searchModel;
        //                this.action.doAction({
        //                    type: "ir.actions.client",
        //                    tag: "import",
        //                    params: { model: resModel, context },
        //                });
        this._OpenWizard();
    }












}
