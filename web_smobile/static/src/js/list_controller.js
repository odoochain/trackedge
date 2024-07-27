/**
    Create by GreenSystem on 22/05/2021
*/
odoo.define('web_smobile.ListController', function (require) {
    'use strict'

    var ListController = require('web.ListController');
    ListController.include({
        start: function () {
            this.$el.addClass('o_list_controller');
            return this._super.apply(this, arguments);
        }
    });
    return ListController;
});
