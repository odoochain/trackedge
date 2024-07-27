/**
    Create by GreenSystem on 22/03/2021
*/
odoo.define('web_smobile.PivotController', function (require) {
    'use strict'
    var PivotController = require('web.PivotController')
    PivotController.include({
        start: function () {
            this.$el.addClass('o_pivot_controller');
            return this._super.apply(this, arguments);
        }
    })
});
