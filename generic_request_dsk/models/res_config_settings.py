# Copyright 2024 Trackedge

from odoo import models, fields, api, _


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    only_create_receiving_request_via_helpdesk = fields.Boolean(
        string='Only Create Receiving Request Via Helpdesk'
    )
    only_create_shipping_request_via_helpdesk = fields.Boolean(
        string='Only Create Shipping Request Via Helpdesk'
    )

    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        param_obj = self.env['ir.config_parameter'].sudo()
        res.update(
            only_create_receiving_request_via_helpdesk=param_obj.get_param('only_create_receiving_request_via_helpdesk'),
            only_create_shipping_request_via_helpdesk=param_obj.get_param('only_create_shipping_request_via_helpdesk')
        )
        return res

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        param_obj = self.env['ir.config_parameter'].sudo()
        param_obj.set_param('only_create_receiving_request_via_helpdesk', self.only_create_receiving_request_via_helpdesk)
        param_obj.set_param('only_create_shipping_request_via_helpdesk', self.only_create_shipping_request_via_helpdesk)
        return res
