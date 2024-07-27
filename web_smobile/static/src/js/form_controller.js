/**
    Create by GreenSystem on 22/03/2021
*/
odoo.define('web_smobile.FormController', function (require) {
    'use strict'

    var FormController = require('web.FormController');
    FormController.include({
        start: function () {
            this.$el.addClass('o_form_controller');
            return this._super.apply(this, arguments);
        }
    })
});
