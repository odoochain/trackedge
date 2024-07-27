# Copyright 2024 Trackedge <https://trackedgetechnologies.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models, api
from odoo.exceptions import ValidationError
from re import findall


class Partner(models.Model):
    _inherit = "res.partner"

    @api.depends('ticket_ids')
    def _ticket_count(self):
        for rec in self:
            rec.ticket_count = len(rec.ticket_ids)

    ticket_count = fields.Integer(
        compute='_ticket_count',
        store=True,
    )
    ticket_ids = fields.One2many(
        'request.request',
        'partner_id',
        string='Servicedesk Ticket',
        readonly=True,
    )
    name = fields.Char(required=True)
    is_servicedesk = fields.Boolean(string="Helpdesk")


    def show_ticket(self):
        for rec in self:
            res = self.env.ref(
                'generic_request.action_request_window')
            res = res.read()[0]
            res['domain'] = str([('partner_id', '=', rec.id)])
        return res




