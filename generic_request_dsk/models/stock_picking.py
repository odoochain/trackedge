# Copyright 2022 Trackedge
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = "stock.picking"

    servicedesk_id = fields.Many2one('request.request', 'Helpdesk')

    @api.onchange('servicedesk_id')
    def _onchange_servicedesk_id(self):
        if self.servicedesk_id and self.servicedesk_id.tt_no:
            self.hd_ticket = self.servicedesk_id.tt_no

    @api.model
    def create(self, vals):
        param_obj = self.env['ir.config_parameter'].sudo()
        receive_hd = param_obj.get_param('only_create_receiving_request_via_helpdesk')
        ship_hd = param_obj.get_param('only_create_shipping_request_via_helpdesk')
        if 'params' in self.env.context and self.env.context['params']['model'] == 'stock.picking':
            pick_type = vals['pick_type']
            if receive_hd and pick_type == 'incoming':
                raise UserError('NPS Requires You to create a ticket first for '
                                'it to automatically create a Receiving Request/Order!')
            if ship_hd and pick_type == 'outgoing':
                raise UserError('NPS Requires You to create a ticket first for '
                                'it to automatically create a Shipping Request/Order!')
        return super(StockPicking, self).create(vals)

