/**
    Create by GreenSystem on 22/05/2021
*/
odoo.define('web_smobile.KanbanController', function (require) {
    'use strict'

    var KanbanController = require('web.KanbanController');
    KanbanController.include({
        start: function () {
            this.$el.addClass('o_kanban_controller');
            return this._super.apply(this, arguments);
        }
    });
    return KanbanController;
});
