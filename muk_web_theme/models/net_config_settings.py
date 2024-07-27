# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    app_system_name = fields.Char('System Name')
    app_show_debug = fields.Boolean('Show Quick Debug', help=u"When enable,everyone login can see the debug menu",
                                    default=False)
    app_show_documentation = fields.Boolean('Show Documentation', help=u"When enable,User can visit user manual")

    app_show_support = fields.Boolean(
        string='Show Support',
        help="When enable User can visit your support site",
        default=True
    )
    app_show_account = fields.Boolean('Show My Account', help=u"When enable,User can login to your website")
    app_show_enterprise = fields.Boolean('Show Enterprise Tag', help=u"Uncheck to hide the Enterprise tag")

    app_documentation_url = fields.Char('Documentation Url')
    app_documentation_dev_url = fields.Char('Developer Documentation Url')
    app_support_url = fields.Char('Support Url')
    app_account_title = fields.Char('My Odoo.com Account Title')
    app_account_url = fields.Char('My Odoo.com Account Url')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        ir_config = self.env['ir.config_parameter'].sudo()
        app_system_name = ir_config.get_param('app_system_name', default='Trackedge')

        app_show_debug = True if ir_config.get_param('app_show_debug') == "False" else True
        app_show_documentation = True if ir_config.get_param('app_show_documentation') == "True" else False
        app_show_support = True #if ir_config.get_param('app_show_support') == "True" else False
        app_show_account = True if ir_config.get_param('app_show_account') == "True" else False
        app_show_enterprise = True if ir_config.get_param('app_show_enterprise') == "True" else False

        app_documentation_url = ir_config.get_param(
            'app_documentation_url', default='https://web.trackedgetech.com')
        app_support_url = ir_config.get_param('app_support_url', default='https://web.trackedgetech.com')
        app_account_title = ir_config.get_param('app_account_title')
        app_account_url = ir_config.get_param('app_account_url', default='https://web.trackedgetech.com')
        res.update(
            app_system_name=app_system_name,
            app_show_debug=app_show_debug,
            app_show_documentation=app_show_documentation,
            app_show_support=app_show_support,
            app_show_account=app_show_account,
            app_show_enterprise=app_show_enterprise,


            app_documentation_url=app_documentation_url,
            app_support_url=app_support_url,
            app_account_title=app_account_title,
            app_account_url=app_account_url,
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        ir_config = self.env['ir.config_parameter'].sudo()
        ir_config.set_param("app_system_name", self.app_system_name or "")
        ir_config.set_param("app_show_debug", self.app_show_debug or "False")
        ir_config.set_param("app_show_documentation", self.app_show_documentation or "False")
        ir_config.set_param("app_show_support", self.app_show_support or "True")
        ir_config.set_param("app_show_account", self.app_show_account or "False")
        ir_config.set_param("app_show_enterprise", self.app_show_enterprise or "False")

        ir_config.set_param("app_documentation_url",self.app_documentation_url or "https://web.trackedgetech.com")
        ir_config.set_param("app_support_url", self.app_support_url or "https://web.trackedgetech.com")
        ir_config.set_param("app_account_title", self.app_account_title or "")
        ir_config.set_param("app_account_url", self.app_account_url or "https://web.trackedgetech.com")

    def set_module_url(self):
        sql = "UPDATE ir_module_module SET website = '%s' WHERE license like '%s' and website <> ''" % (self.app_enterprise_url, 'OEEL%')
        try:
            self._cr.execute(sql)
        except Exception as e:
            pass
