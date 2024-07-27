/**
 @coding: utf-8
 @author: 'GreenSystem'
 */

odoo.define('lyosa_web.menu', function (require) {
    'use strict';
    let AppsMenu = require('web.AppsMenu');
    let SystrayMenu = require('web.SystrayMenu');
    let dom = require('web.dom');
    let core = require('web.core');
    let Widget = require('web.Widget');
    let Menu = require('web.Menu');

    let Menu_Init = Menu.prototype.init;
    let Widget_Start = Widget.prototype.start;

    Menu.include({
        init: function (parent, menu_data) {
            Menu_Init.apply(this, arguments);
            this.$active_menu = false;
        },
        change_menu_section: function (primary_menu_id) {
            if (!this.$menu_sections[primary_menu_id]) {
                this._updateMenuBrand();
                return; // unknown menu_id
            }

            if (this.current_primary_menu === primary_menu_id) {
                return; // already in that menu
            }

            if (this.current_primary_menu) {
                this.$menu_sections[this.current_primary_menu].detach();
            }

            // Get back the application name
            for (var i = 0; i < this.menu_data.children.length; i++) {
                if (this.menu_data.children[i].id === primary_menu_id) {
                    this._updateMenuBrand(this.menu_data.children[i].name);
                    break;
                }
            }

            this.$menu_sections[primary_menu_id].appendTo(this.$section_placeholder);
            if (this.$active_menu) this.$active_menu.removeClass('active');
            this.$active_menu = $(this.$menu_sections[primary_menu_id][0]);
            this.$active_menu.addClass('active');
            this.current_primary_menu = primary_menu_id;

            core.bus.trigger('resize');
        },
        start: function () {
            var self = this;

            this.$menu_apps = this.$('.o_menu_apps');
            this.$menu_brand_placeholder = this.$('.o_menu_brand');
            this.$section_placeholder = this.$('.o_menu_sections');

            // Navbar's menus event handlers
            var on_secondary_menu_click = function (ev) {
                ev.preventDefault();
                var menu_id = $(ev.currentTarget).data('menu');
                var action_id = $(ev.currentTarget).data('action-id');
                if (this.$active_menu) this.$active_menu.removeClass('active');
                this.$active_menu = $(ev.currentTarget).parent();
                this.$active_menu.addClass('active');
                self._on_secondary_menu_click(menu_id, action_id);
            };
            var menu_ids = _.keys(this.$menu_sections);
            var primary_menu_id, $section;
            for (var i = 0; i < menu_ids.length; i++) {
                primary_menu_id = menu_ids[i];
                $section = this.$menu_sections[primary_menu_id];
                $section.on('click', 'a[data-menu]', self, on_secondary_menu_click.bind(this));
            }

            // Apps Menu
            this._appsMenu = new AppsMenu(self, this.menu_data);
            this._appsMenu.appendTo(this.$menu_apps);

            // Systray Menu
            this.systray_menu = new SystrayMenu(this);
            this.systray_menu.attachTo(this.$('.o_menu_systray'));

            dom.initAutoMoreMenu(this.$section_placeholder, {
                maxWidth: function () {
                    return self.$el.width() - (self.$menu_apps.outerWidth(true) + self.$menu_brand_placeholder.outerWidth(true) + self.systray_menu.$el.outerWidth(true));
                },
                sizeClass: 'SM',
            });

            return Widget_Start.apply(this, arguments);
        },
    });
    return Menu;
});