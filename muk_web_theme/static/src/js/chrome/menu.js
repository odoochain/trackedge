/**********************************************************************************
*
*    Copyright (c) 2017-today MuK IT GmbH.
*
*    This file is part of MuK Grid Snippets
*    (see https://mukit.at).
*
*    This program is free software: you can redistribute it and/or modify
*    it under the terms of the GNU Lesser General Public License as published by
*    the Free Software Foundation, either version 3 of the License, or
*    (at your option) any later version.
*
*    This program is distributed in the hope that it will be useful,
*    but WITHOUT ANY WARRANTY; without even the implied warranty of
*    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*    GNU Lesser General Public License for more details.
*
*    You should have received a copy of the GNU Lesser General Public License
*    along with this program. If not, see <http://www.gnu.org/licenses/>.
*
**********************************************************************************/

odoo.define('muk_web_theme.Menu', function (require) {
"use strict";

const config = require("web.config");

const Menu = require("web.Menu");
const AppsBar = require("muk_web_theme.AppsBar");

Menu.include({
    events: _.extend({}, Menu.prototype.events, {
        "click #sidebar-collapse-button": "_onCollapseSidebar",
    	"click .o_menu_apps a[data-toggle=dropdown]": "_onAppsMenuClick",
    	"click .nav-item": "_onNavItemClick",
    	"click .ul_menu_secondary > li > a": "_onItemMenuClick",
    	"click .ul_menu_secondary_submenu > li > a": "_onItemMenuClick",
    	"click .mk_menu_mobile_section": "_onMobileSectionClick",
        "click .o_menu_sections [role=menuitem]": "_hideMobileSubmenus",
        "show.bs.dropdown .o_menu_systray, .o_menu_apps": "_hideMobileSubmenus",
    }),
    menusTemplate: config.device.isMobile ?
    		'muk_web_theme.MobileMenu.sections' : Menu.prototype.menusTemplate,
    start() {
    	const res = this._super(...arguments);
        this.$menu_toggle = this.$(".mk_menu_sections_toggle");
        this.$menu_apps_sidebar = this.$('.mk_apps_sidebar_panel');
        this._appsBar = new AppsBar(this, this.menu_data);
        const appsBarProm = this._appsBar.appendTo(this.$menu_apps_sidebar);
        appsBarProm.then(() => {
            this.$menu_apps_sidebar.renderScrollBar();
            let session = this.getSession();
            let $client_company_logo = $('.oe_client_company_logo');
            let $home_client_company_logo = $('.home_oe_client_company_logo');
            let $home_client_company_logo_mobile = $('.home_oe_client_company_logo_mobile');
            let client_company_logo_src = session.url('/web/image', {
                model:'res.company',
                field: 'logo',
                id: session.company_id,
            });
            let client_company_logo_mobile_src = session.url('/web/image', {
                model:'res.company',
                field: 'logo_mobile',
                id: session.company_id,
            });
            $client_company_logo.attr('src', client_company_logo_src);
            $home_client_company_logo.attr('src', client_company_logo_src);
            $home_client_company_logo_mobile.attr('src', client_company_logo_mobile_src);
        });
        if (config.device.isMobile) {
            const menu_ids = _.keys(this.$menu_sections);
            for (let i = 0; i < menu_ids.length; i++) {
            	const $section = this.$menu_sections[menu_ids[i]];
            	$section.on('click', 'a[data-menu]', this, (ev) => {
                	ev.stopPropagation();
                });
            }
        }
        return Promise.all([
        	res, appsBarProm
        ]);
    },
    change_menu_section(primary_menu_id) {
        // Patch for hiding sub menu
        let menu = this.menu_data.children.find(
            (x)=> x.id == primary_menu_id && x.children.length !=0) || false;
        let container = this.$menu_toggle;
        if (container.length != 0) {
                if (!menu && container.hasClass('d-md-none')) {
                    container.removeClass('d-md-none').addClass('d-none');
                }
                if (menu && container.hasClass('d-none')) {
                     container.removeClass('d-none').addClass('d-md-none');
                }
            }
        return this._super.apply(this, arguments);
    },
    _onCollapseSidebar(){
        $('body').toggleClass('mk_sidebar_type_large');
        $('body').toggleClass('mk_sidebar_type_small');
        let icon = $('#sidebar-collapse-button').find('i');
        icon.toggleClass('fa-bars');
        is_collapsed = true
    },
    _hideMobileSubmenus() {
        if (this.$menu_toggle.is(":visible") && $('.oe_wait').length === 0 && 
        		this.$section_placeholder.is(":visible")) {
            this.$section_placeholder.collapse("hide");
        }
    },
    _updateMenuBrand() {
        return !config.device.isMobile ? this._super(...arguments) : null;
//        return config.device.isMobile ? this._super(...arguments) : null;
    },
    _onAppsMenuClick(event, checkedCanBeRemoved) {
    	const action_manager = this.getParent().action_manager;
    	const controller = action_manager.getCurrentController();
    	if (controller && !checkedCanBeRemoved) {
    		controller.widget.canBeRemoved().then(() => {
    			$(event.currentTarget).trigger('click', [true]);
    			$(event.currentTarget).off('.bs.dropdown');
            });
        	event.stopPropagation();
        	event.preventDefault();
        }
    },
    _onNavItemClick: function (event) {
        $('.active-nav-menu').removeClass('active-nav-menu');
        var $menu = $(event.currentTarget);
        $menu.toggleClass('active-nav-menu');
    },
    _onItemMenuClick: function (event) {
        $('.active-menu').removeClass('active-menu');
        var $menu = $(event.currentTarget);
        $menu.toggleClass('active-menu');
    },
    _onMobileSectionClick(event) {
    	event.preventDefault();
    	event.stopPropagation();
    	const $section = $(event.currentTarget);
    	if ($section.hasClass('show')) {
    		$section.removeClass('show');
    		$section.find('.show').removeClass('show');
    		$section.find('.fa-chevron-down').hide();
    		$section.find('.fa-chevron-right').show();
    	} else {
    		$section.addClass('show');
    		$section.find('ul:first').addClass('show');
    		$section.find('.fa-chevron-down:first').show();
    		$section.find('.fa-chevron-right:first').hide();
    	}
    },
});

});