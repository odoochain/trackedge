# Copyright 2021 Trackedge
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from re import findall

from datetime import date, datetime
from odoo import models, fields, api, _, SUPERUSER_ID, tools
from odoo.exceptions import ValidationError, UserError

CHANNEL = [
    ('web', 'Web'),
    ('email', 'Email'),
    ('phone', 'Phone'),
    ('mobile', 'Mobile App')
]

STATE = [
    ('open', 'Submitted'),
    ('assigned', 'Assigned'),
    ('progress', 'In Progress'),
    ('resolved', 'Resolved'),
    ('closed', 'Closed')
]

PRIORITY = [
    ('0', ''),
    ('1', 'Not Set'),
    ('2', 'Low'),
    ('3', 'Medium'),
    ('4', 'High'),
    ('5', 'Critical')
]

ORIGIN = [
    ('helpdesk', 'Helpdesk'),
    ('crm', 'CRM'),
    ('project', 'Project')
]

CRITICALITY = [
    ('Critical', 'Critical'),
    ('Non Critical', 'Non Critical')
]


class RequestRequest(models.Model):
    _inherit = 'request.request'

    location_longitude = fields.Float(related='site_id.location_longitude')
    location_latitude = fields.Float(related='site_id.location_latitude')
    phone = fields.Char(related='site_id.phone')
    mobile = fields.Char(related='site_id.mobile')
    street = fields.Char(related='site_id.street')
    street2 = fields.Char(related='site_id.street2')
    zip = fields.Char(related='site_id.zip')
    city = fields.Char(related='site_id.city')
    country_id = fields.Many2one('res.country', string="Country")
    state_id = fields.Many2one('res.country.state',
        string="State(Country)", related='site_id.state_id')
    marker_color = fields.Char(related='site_id.marker_color')

    def _expand_states(self, states, domain, order):
        # return all possible states, in order
        return [key for key, val in type(self).state.selection]

    # sla_level_id = fields.Many2one('helpdesk.sla', 'Helpdesk SLA')
    # priority = fields.Selection(
    #     selection=PRIORITY,
    #     string='Ticket Priority',
    #     required=True,
    #     default='2'
    # )
    warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse")
    picking_ids = fields.One2many(
        'stock.picking',
        'servicedesk_id',
        string='Stock Move',
        domain=[('state', '!=', 'cancel')]
    )
    environment = fields.Char("Environment")
    version = fields.Char("Version")
    region_id = fields.Many2one('helpdesk.region', 'Region')
    # region_supervisor_id = fields.Many2one(
    #     # related='region_id.supervisor_id',
    #     string='Region Supervisor'
    # )
    color = fields.Integer(
        'Color Index',
        default=0
    )
    criticality = fields.Selection(selection=CRITICALITY, string="Status",
        default='Non Critical')
    ticket_origin = fields.Selection(selection=ORIGIN, default="helpdesk")
    first_escalation_date = fields.Datetime('First Escalation Date')
    acknowledgement_date = fields.Datetime('Acknowledgement Date')
    reject_date = fields.Datetime('Reject Date')
    reject_reason = fields.Char('Reject Reason')
    update_escalation_date = fields.Datetime('Update Escalation Date')
    solution_escalation_date = fields.Datetime('Solution Escalation Date')
    customer_code = fields.Char('')
    tt_no = fields.Char('NOC TT')
    partner_name = fields.Char(string='Requester company')
    partner_email = fields.Char(string='Customer Email')
    attachments = fields.Binary('')
    new_sla_field = fields.Char()
    shipping_order = fields.Many2one('stock.picking')
    receiving_order = fields.Many2one('stock.picking')
    transfer_order = fields.Many2one('stock.picking')
    msp_company_id = fields.Many2one(
        'res.partner',
        string='MSP Company',
        domain=[('is_company', '=', True)]
    )
    subject = fields.Char(string="Subject")
    soln_bool = fields.Boolean("is Solution esc sent?")
    update_bool = fields.Boolean("is Update esc sent?")
    first_bool = fields.Boolean("is First esc?")
    unlock_bool = fields.Boolean("is Unlock esc?")

    def query_ticket(self, state, name, val):
        if state and name and val == 'followup':
            query = """ select * from helpdesk_ticket where name = '%s'
            and state != '%s';
            """ % (name, state)
            self.env.cr.execute(query)
            result = self.env.cr.dictfetchall()
            if result:
                return result[0]['id']
        if state and name and val == 'reject':
            query = """ select * from helpdesk_ticket where name = '%s'
                   and state = '%s';
                   """ % (name, state)
            self.env.cr.execute(query)
            result = self.env.cr.dictfetchall()
            if result:
                return result[0]['id']
        return False

    @api.model
    def fields_get1(self, fields=None, attributes=None):
        res = super(RequestRequest, self).fields_get1(fields,
                                                     attributes=attributes)
        for field in res:
            if field in ['category']:
                res[field]['sortable'] = False
                res[field]['searchable'] = False
        return res

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        # stages = self.env['helpdesk.stage.config'].search(
        # [('stage_type','=',False)])
        search_domain = [('id', 'in', stages.ids)]
        if 'default_ticket_category' in self.env.context:
            search_domain = ['|', ('ticket_cat_ids', '=', self.env.context[
                'default_ticket_category'])] + search_domain

        stage_ids = stages._search(search_domain, order=order,
                                   access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)
