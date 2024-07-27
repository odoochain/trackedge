odoo.define('muk_web_theme.FormView', function (require) {
"use strict";

const config = require("web.config");
const FormView = require('web.FormView');
const Loading = require('web.Loading');
const QuickCreateFormView = require('web.QuickCreateFormView');
var FormController = require('web.FormController');
var _t = core._t;

FormView.include({
    init() {
        this._super(...arguments);
//        debugger;
        if (config.device.isMobile) {
            this.controllerParams.disableAutofocus = true;
        }
    },
});

QuickCreateFormView.include({
    init() {
        this._super(...arguments);
        if (config.device.isMobile) {
            this.controllerParams.disableAutofocus = true;
        }
    },
});

FormController.include({
    _onButtonClicked: function (ev) {
        let self = this;
        this._super(ev);
        if (ev.data.attrs.history){
            this.btn_history_back = true;
        }
    },
    update: async function (params, options) {
        if ('currentId' in params && !params.currentId) {
            this.mode = 'edit'; // if there is no record, we are in 'edit' mode
        }
        params = _.extend({viewType: 'form', mode: this.mode}, params);
        await this._super(params, options);
        this.autofocus();
        if (this.btn_history_back){
            this.trigger_up('history_back');
            this.btn_history_back = false;
        }
    },
});

});
