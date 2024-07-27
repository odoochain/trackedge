odoo.define('app_odoo_customize.UserMenu', function (require) {
    "use strict";

    /**
     * This widget is appended by the webclient to the right of the navbar.
     * It displays the avatar and the name of the logged user (and optionally the
     * db name, in debug mode).
     * If clicked, it opens a dropdown allowing the user to perform actions like
     * editing its preferences, accessing the documentation, logging out...
     */

    var UserMenu = require('web.UserMenu');

    var documentation_url = 'https://web.trackedgetech.com';
    var documentation_dev_url = 'https://web.trackedgetech.com';
    var support_url = 'https://web.trackedgetech.com';
    var account_title = 'My Account';
    var account_url = 'https://web.trackedgetech.com';

    UserMenu.include({
        init: function () {
            this._super.apply(this, arguments);
            var self = this;
            var session = this.getSession();
            var lang_list = '';


            self._rpc({
                model: 'ir.config_parameter',
                method: 'search_read',
                domain: [['key', '=like', 'app_%']],
                fields: ['key', 'value'],
                lazy: false,
            }).then(function (res) {
                $.each(res, function (key, val) {
                    if (val.key == 'app_documentation_url')
                        documentation_url = val.value;
                    if (val.key == 'app_documentation_dev_url')
                        documentation_dev_url = val.value;
                    if (val.key == 'app_support_url')
                        support_url = val.value;
                    if (val.key == 'app_account_title')
                        account_title = val.value;
                    if (val.key == 'app_account_url')
                        account_url = val.value;

                    if (session.user_context.uid > 2 || (val.key == 'app_show_debug' && val.value == "False")) {
                        $('[data-menu="debug"]').hide();
                        $('[data-menu="debugassets"]').hide();
                        $('[data-menu="quitdebug"]').hide();
                    }
                    if (val.key == 'app_show_documentation' && val.value == "False") {
                        $('[data-menu="documentation"]').hide();
                    }
                    if (val.key == 'app_show_documentation_dev' && val.value == "False") {
                        $('[data-menu="documentation_dev"]').hide();
                    }
                    if (val.key == 'app_show_support' && val.value == "False") {
                        $('[data-menu="support"]').hide();
                    }
                    if (val.key == 'app_show_account' && val.value == "False") {
                        $('[data-menu="account"]').hide();
                    }
                    if (val.key == 'app_account_title' && val.value) {
                        $('[data-menu="account"]').html(account_title);
                    }
                    if (val.key == 'app_show_poweredby' && val.value == "False") {
                        $('.o_sub_menu_footer').hide();
                    }
                });
            })
        },

        start: function () {
            var self = this;
            return this._super.apply(this, arguments).then(function () {

                self.$el.on('click', 'a[data-lang-menu]', function (ev) {
                    ev.preventDefault();
                    var f = self['_onMenuLang']
                    f.call(self, $(this));
                });

                var mMode = 'normal';
                if (window.location.href.indexOf('debug') != -1)
                    mMode = 'debug';
                if (window.location.href.indexOf('debug=assets') != -1)
                    mMode = 'assets';
                if (mMode == 'normal')
                    $('[data-menu="quitdebug"]').hide();
                if (mMode == 'debug')
                    $('[data-menu="debug"]').hide();
                if (mMode == 'assets')
                    $('[data-menu="debugassets"]').hide();
            });
        },
        _onMenuAccount: function () {
            window.open(account_url, '_blank');
        },
        _onMenuDocumentation: function () {
            window.open(documentation_url, '_blank');
        },
        _onMenuSupport: function () {
            window.open(support_url, '_blank');
        },

        _onMenuDebug: function () {
            window.location = $.param.querystring(window.location.href, 'debug=1');
        },
        _onMenuDebugassets: function () {
            window.location = $.param.querystring(window.location.href, 'debug=assets');
        },
        _onMenuQuitdebug: function () {
            window.location.search = "?";
        },
        _onMenuDocumentation_dev: function () {
            window.open(documentation_dev_url, '_blank');
        },
        _onMenuLang: function (ev) {
            var self = this;
            var lang = ($(ev).data("lang-id"));
            var session = this.getSession();
            return this._rpc({
                model: 'res.users',
                method: 'write',
                args: [session.uid, {'lang': lang}],
            }).then(function (result) {
                self.do_action({
                    type: 'ir.actions.client',
                    res_model: 'res.users',
                    tag: 'reload_context',
                    target: 'current',
                });
            });
        },
    })

});
