import json
import logging
import requests
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from .request_request import (AVAILABLE_PRIORITIES,
                              AVAILABLE_IMPACTS,
                              AVAILABLE_URGENCIES)


class RequestType(models.Model):
    _name = "request.type"
    _inherit = [
        'mail.thread',
        'generic.mixin.name_with_code',
        'generic.mixin.track.changes',
    ]
    _description = "Request Type"

    name = fields.Char(copy=False)
    code = fields.Char(copy=False)
    kind_id = fields.Many2one('request.kind', index=True)
    active = fields.Boolean(default=True, index=True)
    description = fields.Text(translate=True)
    note_html = fields.Html(
        translate=True,
        help="Short note about request type, that will"
             " be displayed just before request text.")
    instruction_html = fields.Html(translate=True)
    default_request_text = fields.Html(translate=True)
    help_html = fields.Html(translate=True)
    category_ids = fields.Many2many(
        'request.category',
        'request_type_category_rel', 'type_id', 'category_id',
        'Categories', required=False, index=True)

    tag_category_ids = fields.Many2many(
        'generic.tag.category', 'request_type_tag_category_rel',
        'type_id', 'category_id', string='Tag Categories',
        domain=[('model_id.model', '=', 'request.request')],
        help='Restrict available tags for requests of this type '
             'by these categories')

    # Priority configuration
    complex_priority = fields.Boolean(
        default=False,
        help="When creating request, users select "
             "Impact and Urgency of request. Priority "
             "will be automatically computed depending on "
             "these parameters"
    )
    default_priority = fields.Selection(
        selection=AVAILABLE_PRIORITIES,
        default='3'
    )
    default_impact = fields.Selection(
        selection=AVAILABLE_IMPACTS,
        default='2'
    )
    default_urgency = fields.Selection(
        selection=AVAILABLE_URGENCIES,
        default='2'
    )

    # Stages
    stage_ids = fields.One2many(
        'request.stage', 'request_type_id', string='Stages', copy=True)
    stage_count = fields.Integer(
        compute='_compute_stage_count', readonly=True)
    start_stage_id = fields.Many2one(
        'request.stage', ondelete='set null',
        compute='_compute_start_stage_id', readonly=True, store=True,
        help="The initial stage for new requests of this type. To change, "
             "on the Stages page, click the crossed arrows icon and drag "
             "the desired stage to the top of the list.")
    color = fields.Char(default='rgba(240,240,240,1)')
    is_market_place = fields.Boolean('Is Marketplace Type?')
    # create_local_ticket = fields.Boolean('Create Matching Local Tickets')
    # local_ticket_instance_id = fields.Many2one('nps.instance.connect')
    # local_ticket_instance_id = fields.Many2one('res.partner')
    # Routes
    route_ids = fields.One2many(
        'request.stage.route', 'request_type_id',
        string='Stage Routes')
    route_count = fields.Integer(
        'Routes', compute='_compute_route_count', readonly=True)

    sequence_id = fields.Many2one(
        'ir.sequence', 'Sequence', ondelete='restrict',
        help="Use this sequence to generate names for requests for this type")

    # Access rignts
    access_group_ids = fields.Many2many(
        'res.groups', string='Access groups',
        help="If user belongs to one of groups specified in this field,"
             " then he will be able to select this type during request"
             " creation, even if this category is not published."
    )
    # Requests
    request_ids = fields.One2many(
        'request.request', 'type_id', 'Requests', readonly=True, copy=False)
    request_count = fields.Integer(
        'All Requests', compute='_compute_request_count', readonly=True)
    request_open_count = fields.Integer(
        compute="_compute_request_count", readonly=True,
        string="Open Requests")
    request_closed_count = fields.Integer(
        compute="_compute_request_count", readonly=True,
        string="Closed Requests")
    # Open requests
    request_open_today_count = fields.Integer(
        compute="_compute_request_count", readonly=True,
        string="New Requests For Today")
    request_open_last_24h_count = fields.Integer(
        compute="_compute_request_count", readonly=True,
        string="New Requests For Last 24 Hour")
    request_open_week_count = fields.Integer(
        compute="_compute_request_count", readonly=True,
        string="New Requests For Week")
    request_open_month_count = fields.Integer(
        compute="_compute_request_count", readonly=True,
        string="New Requests For Month")
    # Closed requests
    request_closed_today_count = fields.Integer(
        compute="_compute_request_count", readonly=True,
        string="Closed Requests For Today")
    request_closed_last_24h_count = fields.Integer(
        compute="_compute_request_count", readonly=True,
        string="Closed Requests For Last 24 Hour")
    request_closed_week_count = fields.Integer(
        compute="_compute_request_count", readonly=True,
        string="Closed Requests For Week")
    request_closed_month_count = fields.Integer(
        compute="_compute_request_count", readonly=True,
        string="Closed Requests For Month")
    # Deadline requests
    request_deadline_today_count = fields.Integer(
        compute="_compute_request_count", readonly=True,
        string="Deadline Requests For Today")
    request_deadline_last_24h_count = fields.Integer(
        compute="_compute_request_count", readonly=True,
        string="Deadline Requests For Last 24 Hour")
    request_deadline_week_count = fields.Integer(
        compute="_compute_request_count", readonly=True,
        string="Deadline Requests For Week")
    request_deadline_month_count = fields.Integer(
        compute="_compute_request_count", readonly=True,
        string="Deadline Requests For Month")
    # Unassigned requests
    request_unassigned_count = fields.Integer(
        compute="_compute_request_count", readonly=True,
        string="Unassigned Requests")

    # Notification Settins
    send_default_created_notification = fields.Boolean(default=True)
    created_notification_show_request_text = fields.Boolean(default=True)
    created_notification_show_response_text = fields.Boolean(default=False)
    send_default_assigned_notification = fields.Boolean(default=True)
    assigned_notification_show_request_text = fields.Boolean(default=True)
    assigned_notification_show_response_text = fields.Boolean(default=False)
    send_default_created_uat = fields.Boolean(default=True)
    uat_notification_show_request_text = fields.Boolean(default=True)
    uat_notification_show_response_text = fields.Boolean(default=True)
    send_default_closed_notification = fields.Boolean(default=True)
    closed_notification_show_request_text = fields.Boolean(default=True)
    closed_notification_show_response_text = fields.Boolean(default=True)
    send_default_reopened_notification = fields.Boolean(default=True)
    reopened_notification_show_request_text = fields.Boolean(default=True)
    reopened_notification_show_response_text = fields.Boolean(default=False)
    remote_id = fields.Integer()
    # auto_create_receiving_request = fields.Boolean()
    auto_create_shipping_request = fields.Boolean()
    is_routine_ticket_type = fields.Boolean()
    auto_create_routine = fields.Boolean()
    auto_create_routine_model_id = fields.Many2one('ir.model')
    auto_create_routine_code = fields.Char()

    # Timesheets
    use_timesheet = fields.Boolean()
    timesheet_activity_ids = fields.Many2many(
        comodel_name='request.timesheet.activity',
        relation='request_type__timesheet_activity__rel',
        column1='request_type_id',
        column2='activity_id')
    team_ids = fields.Many2many(
        comodel_name="res.users",
        string="Team",
    )
    default_assignee_id = fields.Many2one('res.users', 'Default Assignee')

    _sql_constraints = [
        ('name_uniq',
         'UNIQUE (name)',
         'Name must be unique.'),
        ('code_uniq',
         'UNIQUE (code)',
         'Code must be unique.'),
    ]

    @api.depends('request_ids')
    def _compute_request_count(self):
        RequestRequest = self.env['request.request']
        now = datetime.now()
        for record in self:
            record.request_count = len(record.request_ids)
            record.request_closed_count = RequestRequest.search_count([
                ('closed', '=', True),
                ('type_id', '=', record.id)
            ])
            record.request_open_count = RequestRequest.search_count([
                ('closed', '=', False),
                ('type_id', '=', record.id)
            ])

            today_start = now.replace(
                hour=0, minute=0, second=0, microsecond=0)
            yesterday = now - relativedelta(days=1)
            week_ago = now - relativedelta(weeks=1)
            month_ago = now - relativedelta(months=1)
            # Open requests
            record.request_open_today_count = RequestRequest.search_count([
                ('date_created', '>=', today_start),
                ('closed', '=', False),
                ('type_id', '=', record.id)
            ])
            record.request_open_last_24h_count = RequestRequest.search_count([
                ('date_created', '>', yesterday),
                ('closed', '=', False),
                ('type_id', '=', record.id)
            ])
            record.request_open_week_count = RequestRequest.search_count([
                ('date_created', '>', week_ago),
                ('closed', '=', False),
                ('type_id', '=', record.id)
            ])
            record.request_open_month_count = RequestRequest.search_count([
                ('date_created', '>', month_ago),
                ('closed', '=', False),
                ('type_id', '=', record.id)
            ])
            # Closed requests
            record.request_closed_today_count = RequestRequest.search_count([
                ('date_closed', '>=', today_start),
                ('closed', '=', True),
                ('type_id', '=', record.id)
            ])
            record.request_closed_last_24h_count = (
                RequestRequest.search_count([
                    ('date_closed', '>', yesterday),
                    ('closed', '=', True),
                    ('type_id', '=', record.id)
                ]))
            record.request_closed_week_count = RequestRequest.search_count([
                ('date_closed', '>', week_ago),
                ('closed', '=', True),
                ('type_id', '=', record.id)
            ])
            record.request_closed_month_count = RequestRequest.search_count([
                ('date_closed', '>', month_ago),
                ('closed', '=', True),
                ('type_id', '=', record.id)
            ])
            # Deadline requests
            record.request_deadline_today_count = RequestRequest.search_count([
                ('deadline_date', '>=', today_start),
                ('closed', '=', False),
                ('type_id', '=', record.id)
            ])
            record.request_deadline_last_24h_count = (
                RequestRequest.search_count([
                    ('deadline_date', '>', yesterday),
                    ('closed', '=', False),
                    ('type_id', '=', record.id)
                ]))
            record.request_deadline_week_count = RequestRequest.search_count([
                ('deadline_date', '>', week_ago),
                ('closed', '=', False),
                ('type_id', '=', record.id)
            ])
            record.request_deadline_month_count = RequestRequest.search_count([
                ('deadline_date', '>', month_ago),
                ('closed', '=', False),
                ('type_id', '=', record.id)
            ])
            # Unassigned requests
            record.request_unassigned_count = RequestRequest.search_count([
                ('user_id', '=', False),
                ('type_id', '=', record.id)
            ])

    @api.depends('stage_ids')
    def _compute_stage_count(self):
        for record in self:
            record.stage_count = len(record.stage_ids)

    @api.depends('route_ids')
    def _compute_route_count(self):
        for record in self:
            record.route_count = len(record.route_ids)

    @api.depends('stage_ids', 'stage_ids.sequence',
                 'stage_ids.request_type_id')
    def _compute_start_stage_id(self):
        """ Compute start stage for requests of this type
            using following logic:

            - stages have field 'sequence'
            - stages are ordered by value of this field.
            - it is possible from ui to change stage order by dragging them
            - get first stage for stages related to this type

        """
        for rtype in self:
            if rtype.stage_ids:
                rtype.start_stage_id = rtype.stage_ids.sorted(
                    key=lambda r: r.sequence)[0]
            else:
                rtype.start_stage_id = False

    def _create_default_stages_and_routes(self):
        self.ensure_one()
        stage_new = self.env['request.stage'].create({
            'name': _('New'),
            'code': 'new',
            'request_type_id': self.id,
            'sequence': 5,
            'type_id': self.env.ref(
                'generic_request.request_stage_type_draft').id,
        })
        stage_assigned = self.env['request.stage'].create({
            'name': _('Assigned'),
            'code': 'assigned',
            'request_type_id': self.id,
            'sequence': 6,
            'type_id': self.env.ref(
                'generic_request.request_stage_type_assigned').id,
        })
        stage_cancel = self.env['request.stage'].create({
            'name': _('Cancel'),
            'code': 'cancel',
            'request_type_id': self.id,
            'sequence': 6,
            'type_id': self.env.ref(
                'generic_request.request_stage_type_cancel').id,
        })
        stage_in_progress = self.env['request.stage'].create({
            'name': _('In Progress'),
            'code': 'in-progress',
            'request_type_id': self.id,
            'sequence': 7,
            'type_id': self.env.ref(
                'generic_request.request_stage_type_progress').id,
        })
        stage_in_qc_passed = self.env['request.stage'].create({
            'name': _('QC'),
            'code': 'qc',
            'request_type_id': self.id,
            'sequence': 8,
            'type_id': self.env.ref(
                'generic_request.request_stage_type_qc').id,
        })
        stage_in_uat = self.env['request.stage'].create({
            'name': _('UAT'),
            'code': 'uat',
            'request_type_id': self.id,
            'sequence': 9,
            'type_id': self.env.ref(
                'generic_request.request_stage_type_uat').id,
        })
        stage_in_uat_failed = self.env['request.stage'].create({
            'name': _('UAT Failed'),
            'code': 'uat-failed',
            'request_type_id': self.id,
            'sequence': 10,
            'type_id': self.env.ref(
                'generic_request.request_stage_type_closed_fail').id,
        })
        stage_close = self.env['request.stage'].create({
            'name': _('Done/Closed'),
            'code': 'close',
            'request_type_id': self.id,
            'sequence': 11,
            'closed': True,
            'type_id': self.env.ref(
                'generic_request.request_stage_type_closed_ok').id,
        })
        self.env['request.stage.route'].create({
            'name': _('Assigned'),
            'stage_from_id': stage_new.id,
            'stage_to_id': stage_assigned.id,
            'request_type_id': self.id,
        })
        self.env['request.stage.route'].create({
            'name': _('Cancel'),
            'stage_from_id': stage_assigned.id,
            'stage_to_id': stage_cancel.id,
            'request_type_id': self.id,
        })
        self.env['request.stage.route'].create({
            'name': _('In Progress'),
            'stage_from_id': stage_assigned.id,
            'stage_to_id': stage_in_progress.id,
            'request_type_id': self.id,
        })
        self.env['request.stage.route'].create({
            'name': _('QC'),
            'stage_from_id': stage_in_progress.id,
            'stage_to_id': stage_in_qc_passed.id,
            'request_type_id': self.id,
        })
        self.env['request.stage.route'].create({
            'name': _('UAT'),
            'stage_from_id': stage_in_qc_passed.id,
            'stage_to_id': stage_in_uat.id,
            'request_type_id': self.id,
        })
        self.env['request.stage.route'].create({
            'name': _('UAT Failed'),
            'stage_from_id': stage_in_uat.id,
            'stage_to_id': stage_in_uat_failed.id,
            'request_type_id': self.id,
        })
        self.env['request.stage.route'].create({
            'name': _('Re Assign'),
            'stage_from_id': stage_in_uat_failed.id,
            'stage_to_id': stage_in_qc_passed.id,
            'request_type_id': self.id,
        })
        self.env['request.stage.route'].create({
            'name': _('Re Progress'),
            'stage_from_id': stage_in_qc_passed.id,
            'stage_to_id': stage_in_progress.id,
            'request_type_id': self.id,
        })
        self.env['request.stage.route'].create({
            'name': _('Done'),
            'stage_from_id': stage_in_uat.id,
            'stage_to_id': stage_close.id,
            'request_type_id': self.id,
        })

    @api.model
    def create(self, vals):
        r_type = super(RequestType, self).create(vals)

        if not r_type.start_stage_id and self.env.context.get(
                'create_default_stages'):
            r_type._create_default_stages_and_routes()

        return r_type

    def action_create_default_stage_and_routes(self):
        self._create_default_stages_and_routes()

    def action_request_type_diagram(self):
        self.ensure_one()
        action = self.env['generic.mixin.get.action'].get_action_by_xmlid(
            'generic_request.action_type_window',
            context={'default_request_type_id': self.id},
        )
        action.update({
            'res_model': 'request.type',
            'res_id': self.id,
            'views': [(False, 'diagram_plus'), (False, 'form')],
        })
        return action

    def action_type_request_open_today_count(self):
        self.ensure_one()
        today_start = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0)
        return self.env['generic.mixin.get.action'].get_action_by_xmlid(
            'generic_request.action_stat_request_count',
            domain=[
                ('date_created', '>=', today_start),
                ('closed', '=', False),
                ('type_id', '=', self.id)])

    def action_type_request_open_last_24h_count(self):
        self.ensure_one()
        yesterday = datetime.now() - relativedelta(days=1)
        return self.env['generic.mixin.get.action'].get_action_by_xmlid(
            'generic_request.action_stat_request_count',
            domain=[
                ('date_created', '>', yesterday),
                ('closed', '=', False),
                ('type_id', '=', self.id)])

    def action_type_request_open_week_count(self):
        self.ensure_one()
        week_ago = datetime.now() - relativedelta(weeks=1)
        return self.env['generic.mixin.get.action'].get_action_by_xmlid(
            'generic_request.action_stat_request_count',
            domain=[
                ('date_created', '>', week_ago),
                ('closed', '=', False),
                ('type_id', '=', self.id)])

    def action_type_request_open_month_count(self):
        self.ensure_one()
        month_ago = datetime.now() - relativedelta(months=1)
        return self.env['generic.mixin.get.action'].get_action_by_xmlid(
            'generic_request.action_stat_request_count',
            domain=[
                ('date_created', '>', month_ago),
                ('closed', '=', False),
                ('type_id', '=', self.id)])

    def action_type_request_closed_today_count(self):
        self.ensure_one()
        today_start = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0)
        return self.env['generic.mixin.get.action'].get_action_by_xml(
            'generic_request.action_stat_request_count',
            context={'search_default_filter_closed': 1},
            domain=[
                ('date_closed', '>=', today_start),
                ('closed', '=', True),
                ('type_id', '=', self.id)])

    def action_type_request_closed_last_24h_count(self):
        self.ensure_one()
        yesterday = datetime.now() - relativedelta(days=1)
        return self.env['generic.mixin.get.action'].get_action_by_xml(
            'generic_request.action_stat_request_count',
            context={'search_default_filter_closed': 1},
            domain=[
                ('date_closed', '>', yesterday),
                ('closed', '=', True),
                ('type_id', '=', self.id)])

    def action_type_request_closed_week_count(self):
        self.ensure_one()
        week_ago = datetime.now() - relativedelta(weeks=1)
        return self.env['generic.mixin.get.action'].get_action_by_xml(
            'generic_request.action_stat_request_count',
            context={'search_default_filter_closed': 1},
            domain=[
                ('date_closed', '>', week_ago),
                ('closed', '=', True),
                ('type_id', '=', self.id)])

    def action_type_request_closed_month_count(self):
        self.ensure_one()
        month_ago = datetime.now() - relativedelta(months=1)
        return self.env['generic.mixin.get.action'].get_action_by_xml(
            'generic_request.action_stat_request_count',
            context={'search_default_filter_closed': 1},
            domain=[
                ('date_closed', '>', month_ago),
                ('closed', '=', True),
                ('type_id', '=', self.id)])

    def action_type_request_deadline_today_count(self):
        self.ensure_one()
        today_start = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0)
        return self.env['generic.mixin.get.action'].get_action_by_xmlid(
            'generic_request.action_stat_request_count',
            domain=[
                ('deadline_date', '>=', today_start),
                ('closed', '=', False),
                ('type_id', '=', self.id)])

    def action_type_request_deadline_last_24h_count(self):
        self.ensure_one()
        yesterday = datetime.now() - relativedelta(days=1)
        return self.env['generic.mixin.get.action'].get_action_by_xmlid(
            'generic_request.action_stat_request_count',
            domain=[
                ('deadline_date', '>', yesterday),
                ('closed', '=', False),
                ('type_id', '=', self.id)])

    def action_type_request_deadline_week_count(self):
        self.ensure_one()
        week_ago = datetime.now() - relativedelta(weeks=1)
        return self.env['generic.mixin.get.action'].get_action_by_xmlid(
            'generic_request.action_stat_request_count',
            domain=[
                ('deadline_date', '>', week_ago),
                ('closed', '=', False),
                ('type_id', '=', self.id)])

    def action_type_request_deadline_month_count(self):
        self.ensure_one()
        month_ago = datetime.now() - relativedelta(months=1)
        return self.env['generic.mixin.get.action'].get_action_by_xmlid(
            'generic_request.action_stat_request_count',
            domain=[
                ('deadline_date', '>', month_ago),
                ('closed', '=', False),
                ('type_id', '=', self.id)])

    def action_type_request_unassigned_count(self):
        self.ensure_one()
        return self.env['generic.mixin.get.action'].get_action_by_xmlid(
            'generic_request.action_stat_request_count',
            domain=[
                ('user_id', '=', False),
                ('type_id', '=', self.id)])

    @api.model
    def cron_sync_request_type(self):
        erp = self.env['nps.instance.connect'].search([('code', '=', 'erp')], limit=1)
        token = erp.get_access_token()
        api_url = erp.instance_url + '/api/search_read/request.type?limit=1000'
        headers = {
            'Authorization': 'Bearer %s' % token
        }
        response = requests.get(api_url, headers=headers)
        convertedDict = json.loads(response.text)
        for line in convertedDict:
            existing_record = self.search([('remote_id', '=', line['id'])], limit=1)
            category_ids = []
            if len(line['category_ids']):
                categories = self.env['request.category'].search([('remote_id', 'in', line['category_ids'])])
                if len(categories):
                    category_ids = categories.ids
            start_stage_id = False
            if line['start_stage_id']:
                stage = self.env['request.stage'].search([('remote_id', '=', line['start_stage_id'][0])], limit=1)
                if stage:
                    start_stage_id = stage.id
            vals = {
                'remote_id': line['id'],
                'name': line['name'],
                'active': line['active'],
                'category_ids': category_ids,
                'code': line['code'],
                'start_stage_id': start_stage_id,
                'is_market_place': line['is_market_place'],
                # 'sequence_id': line['sequence_id'],
                'color': line['color'],
                'complex_priority': line['complex_priority'],
                'default_priority': line['default_priority']
            }
            if not existing_record:
                new_record = self.create(vals)
            else:
                existing_record.write(vals)
