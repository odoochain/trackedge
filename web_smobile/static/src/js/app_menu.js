odoo.define('lyosa_web.AppsMenu', function (require) {
    'use strict';
    let Widget = require('web.Widget');
    let AppsMenu = require('web.AppsMenu');
    const rpc = require('web.rpc');

    let WidgetInit = Widget.prototype.init;
    AppsMenu.include({
        init: function (parent, menuData){
            WidgetInit.apply(this, arguments);
            this._activeApp = undefined;
            this._apps = _.map(menuData.children, function (appMenuData) {
                return {
                    actionID: parseInt(appMenuData.action.split(',')[1]),
                    menuID: appMenuData.id,
                    name: appMenuData.name,
                    xmlID: appMenuData.xmlid,
                    web_icon: appMenuData.web_icon,
                };
            });
        },
        getCompanyName: function () {
            var session = this.getSession();
            return session.user_companies.current_company[1]

        }
    });
    return AppsMenu;
});
