/**
    Create by GreenSystem on 22/08/2021
*/
odoo.define('web_smobile.InputField', function (require) {
    'use strict'

    var InputField = require('web.basic_fields').InputField;

    var InputFieldInit = InputField.prototype.init;
    var InputFieldEvents = InputField.prototype.events;

    InputField.include({
        /**
            Add event focus to Input field by add new one to events prototype.
            But this way only apply for normal input field because some input type like phone, email, ...
            will override this class's prototype
            => We need to set events on init() instead
        */
        // events: _.extend({}, InputFieldEvents, {
        //     'focus': '_onFocus'
        // }),

        init: function () {
            this.events = _.extend({}, InputFieldEvents, {
                'focus': '_onFocus'
            }),
            InputFieldInit.apply(this, arguments);
        },

        _onFocus: function () {
            this.$el.select();
        },
    });
    return InputField;
});
