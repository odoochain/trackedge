# pylint:disable=too-many-lines
import json
import pytz
import logging
import requests
from datetime import datetime, timedelta
from odoo import models, fields, api, tools, _, http, exceptions, SUPERUSER_ID
from odoo.addons.generic_mixin import pre_write, post_write, pre_create
from odoo.osv import expression
from odoo.exceptions import ValidationError, UserError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from ..tools.utils import html2text
from json2html import *
from pytz import UTC
from ..constants import (
    TRACK_FIELD_CHANGES,
    REQUEST_TEXT_SAMPLE_MAX_LINES,
    KANBAN_READONLY_FIELDS,
    MAIL_REQUEST_TEXT_TMPL,
    AVAILABLE_PRIORITIES,
    AVAILABLE_IMPACTS,
    AVAILABLE_URGENCIES,
    PRIORITY_MAP,
)
from lxml import etree

_logger = logging.getLogger(__name__)
TRACK_FIELD_CHANGES.update(['parent_id'])


class RequestRequest(models.Model):
    _name = "request.request"
    _inherit = [
        'mail.thread',
        'mail.activity.mixin',
        'generic.mixin.track.changes',
        'generic.tag.mixin',
        'generic.mixin.get.action',
        'portal.mixin',
    ]
    _description = 'Request'
    _order = 'date_created DESC'
    _needaction = True
    _parent_store = True
    _parent_order = 'name'

    name = fields.Char(
        required=True, index=True, readonly=True, default="New", copy=False)
    help_html = fields.Html(
        "Help", related="type_id.help_html", readonly=True)
    category_help_html = fields.Html(
        related='category_id.help_html', readonly=True, string="Category help")
    stage_help_html = fields.Html(
        "Stage help", related="stage_id.help_html", readonly=True)
    instruction_html = fields.Html(
        related='type_id.instruction_html',
        readonly=True, string='Instruction')
    note_html = fields.Html(
        related='type_id.note_html', readonly=True, string="Note")
    active = fields.Boolean(default=True, index=True)

    # Priority
    _priority = fields.Char(
        default='3', readonly=True,
        string='Priority (Technical)')
    priority = fields.Selection(
        selection=AVAILABLE_PRIORITIES,
        tracking=True,
        index=True,
        store=True,
        string='Ticket Priority',
        compute='_compute_priority',
        inverse='_inverse_priority',
        help="Actual priority of request"
    )
    impact = fields.Selection(
        selection=AVAILABLE_IMPACTS,
        index=True
    )
    urgency = fields.Selection(
        selection=AVAILABLE_URGENCIES,
        index=True
    )
    is_priority_complex = fields.Boolean(
        related='type_id.complex_priority', readonly=True)

    # Type and stage related fields
    type_id = fields.Many2one(
        'request.type', 'Type', ondelete='restrict',
        required=True, index=True, tracking=True,
        help="Type of request")
    type_color = fields.Char(related="type_id.color", readonly=True)
    # type_code = fields.Char(related="type_id.code", readonly=True, store=True)
    kind_id = fields.Many2one(
        'request.kind', related='type_id.kind_id',
        store=True, index=True, readonly=True,
        help="Kind of request")
    category_id = fields.Many2one(
        'request.category', 'Category', index=True,
        required=False, ondelete="restrict", tracking=True,
        help="Category of request")
    channel_id = fields.Many2one(
        'request.channel', 'Channel', index=True, required=False,
        default=lambda self: self.env.ref(
            'generic_request.request_channel_other', raise_if_not_found=False),
        help="Channel of request")

    stage_id = fields.Many2one(
        'request.stage', 'Stage', ondelete='restrict',
        required=True, index=True, tracking=True, copy=False
    )
    stage_type_code = fields.Char(related='stage_type_id.code', readonly=True, store=True)

    @api.model
    def _read_group_stage_type_id_ids(self, stages, domain, order):
        stage_ids = self.env['request.stage.type'].search([('is_market_place', '=', False)])
        return stage_ids

    def _get_default_stage_type_id(self):
        """ Gives default stage_id """
        type_obj = self.env['request.stage.type']
        stage_id = type_obj.search([('code', '=', 'new'), ('is_market_place', '=', False)], limit=1).id
        if not stage_id:
            stage_id = type_obj.search([('code', '=', 'draft'), ('is_market_place', '=', True)], limit=1).id
        return stage_id

    def _compute_stage_type_id(self):
        for rec in self:
            if rec.type_id and rec.stage_id:
                rec.stage_type_id = rec.stage_id.type_id.id
            else:
                rec.stage_type_id = False

    def _inverse_stage_type_id(self):
        for rec in self:
            if rec.type_id and rec.stage_type_id:
                rec.stage_id = self.env['request.stage'].search([('request_type_id', '=', rec.type_id.id), ('type_id', '=', rec.stage_type_id.id)], limit=1).id
            else:
                rec.stage_id = False

    stage_type_id = fields.Many2one('request.stage.type', string='Stage', compute='_compute_stage_type_id', inverse='_inverse_stage_type_id',
        store=True, readonly=False, ondelete='restrict', tracking=True, index=True,
        default=_get_default_stage_type_id,
        group_expand='_read_group_stage_type_id_ids',
        copy=False)

    # stage_type_id = fields.Many2one(
    #     'request.stage.type', string="Stage Type", compute='_compute_stage_type_id', inverse='_inverse_stage_type_id',
    #     index=True, readonly=True, store=True,
    #     group_expand='_read_group_stage_type_id_ids'
    # )
    stage_bg_color = fields.Char(
        compute="_compute_stage_colors", string="Stage Background Color")
    stage_label_color = fields.Char(
        compute="_compute_stage_colors")
    last_route_id = fields.Many2one('request.stage.route', 'Last Route')
    closed = fields.Boolean(
        related='stage_id.closed', store=True, index=True, readonly=True)
    can_be_closed = fields.Boolean(
        compute='_compute_can_be_closed', readonly=True)
    is_assigned = fields.Boolean(
        compute="_compute_is_assigned", store=True, readonly=True)

    kanban_state = fields.Selection(
        selection=[
            ('normal', 'In Progress'),
            ('blocked', 'Blocked'),
            ('done', 'Ready for next stage')],
        required='True',
        default='normal',
        tracking=True,
        help="A requests kanban state indicates special"
             " situations affecting it:\n"
             " * Grey is the default situation\n"
             " * Red indicates something is preventing the"
             "progress of this request\n"
             " * Green indicates the request is ready to be pulled"
             "to the next stage")

    # 12.0 compatability. required to generate xmlid for this field
    tag_ids = fields.Many2many()

    # Is this request new (does not have ID yet)?
    # This field could be used in domains in views for True and False leafs:
    # [1, '=', 1] -> True,
    # [0, '=', 1] -> False
    is_new_request = fields.Integer(
        compute='_compute_is_new_request', readonly=True, default=1)

    # UI change restriction fields
    can_change_request_text = fields.Boolean(
        compute='_compute_can_change_request_text', readonly=True,
        compute_sudo=False)
    can_change_assignee = fields.Boolean(
        compute='_compute_can_change_assignee', readonly=True,
        compute_sudo=False)
    can_change_author = fields.Boolean(
        compute='_compute_can_change_author', readonly=True,
        compute_sudo=False)
    can_change_category = fields.Boolean(
        compute='_compute_can_change_category', readonly=True,
        compute_sudo=False)
    can_change_deadline = fields.Boolean(
        compute='_compute_can_change_deadline', readonly=True,
        compute_sudo=False)

    # Request data fields
    request_text = fields.Html(required=True, default="Ticket Details")
    response_text = fields.Html(required=False)
    request_text_sample = fields.Text(
        compute="_compute_request_text_sample", tracking=True,
        string='Request text')

    deadline_date = fields.Date('Deadline')
    deadline_state = fields.Selection(selection=[
        ('ok', 'Ok'),
        ('today', 'Today'),
        ('overdue', 'Overdue')], compute='_compute_deadline_state')
    request_state = fields.Selection(selection=[
        ('normal', 'Normal'),
        ('today', 'Today'),
        ('overdue', 'Overdue')], compute='_get_request_state', store=True)
    max_throughput_stage_time = fields.Float('Max Throughput Time(Hrs)')
    overdue_mail_sent = fields.Boolean('Mail Sent')
    date_created = fields.Datetime(
        'Created', default=fields.Datetime.now, readonly=True, copy=False)
    date_closed = fields.Datetime('Closed', readonly=True, copy=False)
    date_assigned = fields.Datetime('Assigned', readonly=True, copy=False)
    date_assigned_first_time = fields.Datetime('Date Assigned on first User')
    date_moved = fields.Datetime('Moved', readonly=True, copy=False)
    created_by_id = fields.Many2one(
        'res.users', 'Created by', readonly=True, ondelete='restrict',
        default=lambda self: self.env.user, index=True,
        help="Request was created by this user", copy=False)
    moved_by_id = fields.Many2one(
        'res.users', 'Moved by', readonly=True, ondelete='restrict',
        copy=False)
    closed_by_id = fields.Many2one(
        'res.users', 'Closed by', readonly=True, ondelete='restrict',
        copy=False, help="Request was closed by this user")
    partner_id = fields.Many2one(
        'res.partner', 'Partner', index=True, tracking=True,
        ondelete='restrict', help="Partner related to this request")
    author_id = fields.Many2one(
        'res.partner', 'Author', index=True, required=False,
        ondelete='restrict', tracking=True,
        domain=[('is_company', '=', False)],
        default=lambda self: self.env.user.partner_id,
        help="Author of this request")
    user_id = fields.Many2one(
        'res.users', 'Assigned to',
        ondelete='restrict', tracking=True, index=True,
        help="User responsible for next action on this request.")

    # Email support
    email_from = fields.Char(
        'Email', help="Email address of the contact", index=True,
        readonly=True)
    email_cc = fields.Text(
        'Global CC', readonly=True,
        help="These email addresses will be added to the CC field "
             "of all inbound and outbound emails for this record "
             "before being sent. "
             "Separate multiple email addresses with a comma")
    author_name = fields.Char(
        readonly=True,
        help="Name of author based on incoming email")
    author_phone = fields.Char(
        readonly=True,
        help="Phone of author")

    message_discussion_ids = fields.One2many(
        'mail.message', 'res_id', string='Discussion Messages', store=True,
        domain=lambda r: [
            ('subtype_id', '=', r.env.ref('mail.mt_comment').id)])
    original_message_id = fields.Char(
        help='Technical field. '
             'ID of original message that started this request.')
    attachment_ids = fields.One2many(
        'ir.attachment', 'res_id',
        domain=[('res_model', '=', 'request.request')],
        string='Attachments')

    instruction_visible = fields.Boolean(
        compute='_compute_instruction_visible', default=False,
        compute_sudo=False)

    # We have to explicitly set compute_sudo to True to avoid access errors
    activity_date_deadline = fields.Date(compute_sudo=True)

    # Events
    request_event_ids = fields.One2many(
        'request.event', 'request_id', 'Events', readonly=True)
    request_event_count = fields.Integer(
        compute='_compute_request_event_count', readonly=True)

    # Timesheets
    timesheet_line_ids = fields.One2many(
        'request.timesheet.line', 'request_id')
    timesheet_planned_amount = fields.Float(
        help="Planned time")
    timesheet_amount = fields.Float(
        compute='_compute_timesheet_line_data',
        readonly=True, store=True,
        help="Time spent")
    timesheet_remaining_amount = fields.Float(
        compute='_compute_timesheet_line_data',
        readonly=True, store=True,
        help="Remaining time")
    timesheet_progress = fields.Float(
        compute='_compute_timesheet_line_data',
        readonly=True, store=True,
        help="Request progress, calculated as the ratio of time spent "
             "to planned time")
    timesheet_start_status = fields.Selection(
        [('started', 'Started'),
         ('not-started', 'Not Started')],
        compute='_compute_timesheet_start_status', readonly=True)
    use_timesheet = fields.Boolean(
        related='type_id.use_timesheet', readonly=True)

    author_related_request_open_count = fields.Integer(
        compute='_compute_related_a_p_request_ids')
    author_related_request_closed_count = fields.Integer(
        compute='_compute_related_a_p_request_ids')

    partner_related_request_open_count = fields.Integer(
        compute='_compute_related_a_p_request_ids')
    partner_related_request_closed_count = fields.Integer(
        compute='_compute_related_a_p_request_ids')

    stage_route_out_json = fields.Char(
        compute='_compute_stage_route_out_json', readonly=True)

    parent_id = fields.Many2one(
        'request.request', 'Parent', index=True,
        ondelete='restrict', readonly=True,
        tracking=True,
        help="Parent request")
    parent_path = fields.Char(index=True)
    child_ids = fields.One2many(
        'request.request', 'parent_id', 'Subrequests', readonly=True)
    child_count = fields.Integer(
        'Subrequest Count', compute='_compute_child_count')
    jira_url = fields.Char('JIRA URL')
    asana_url = fields.Char('Asana URL')
    ticket_link = fields.Char(compute='compute_ticket_link')
    duration = fields.Float('Taken Time to close', compute='_compute_duration', store=True, readonly=False)
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.user.company_id,
        string='Company',
        readonly=True,
    )
    is_market_place_request = fields.Boolean('Is Marketplace Request?', related='type_id.is_market_place', store=True)
    # create_local_ticket = fields.Boolean(related='type_id.create_local_ticket')
    # local_ticket_instance_id = fields.Many2one(related='type_id.local_ticket_instance_id')
    # auto_create_receiving_request = fields.Boolean(related='type_id.auto_create_receiving_request')
    # auto_create_shipping_request = fields.Boolean(related='type_id.auto_create_shipping_request')
    is_routine_ticket_type = fields.Boolean(related='type_id.is_routine_ticket_type')
    auto_create_routine = fields.Boolean(related='type_id.auto_create_routine')
    auto_create_routine_model_id = fields.Many2one(related='type_id.auto_create_routine_model_id')
    auto_create_routine_code = fields.Char(related='type_id.auto_create_routine_code')
    auto_routine_engineer_id = fields.Many2one('res.users', 'Engineer', tracking=True)
    auto_routine_site_id = fields.Many2one('stock.warehouse', string='Site')
    auto_routine_site_access = fields.Text('Site Access Instruction')
    auto_routine_site_wo = fields.Char('Work Order')
    remote_id = fields.Integer('Global Helpdesk ID')
    remote_ticket_id = fields.Integer()
    remote_ticket_link = fields.Char()
    site_id = fields.Many2one('stock.warehouse', string='Site ID')
    request_stage_ids = fields.Many2many(
        'request.stage.type',
        'request_stage_rel',
        'request_id',
        'stage_id',
        compute='compute_request_stage_ids',
        store=True,
        string='Stages')
    stage_due_date = fields.Datetime('Stage Due Date')
    escalate_user_id = fields.Many2one('res.users', 'Escalate User')
    ticket_escalated = fields.Boolean('Ticket Escalated')

    @api.depends('type_id', 'type_id.stage_ids')
    def compute_request_stage_ids(self):
        for this in self:
            if this.type_id:
                this.request_stage_ids = this.type_id.stage_ids.mapped('type_id').ids
            else:
                this.request_stage_ids = False

    @api.onchange('auto_routine_site_id')
    def _onchange_auto_routine_site_id(self):
        if self.auto_routine_site_id:
            self.site_id = self.auto_routine_site_id.id

    def compute_ticket_link(self):
        for this in self:
            url = "%s/web#id=%s&model=request.request&view_type=form" % (
                self.get_base_url(),
                this.id
            )
            this.ticket_link = url

    def _get_duration(self, start, stop):
        """ Get the duration value between the 2 given dates. """
        if not start or not stop:
            return 0
        duration = (stop - start).total_seconds() / 3600
        return round(duration, 2)


    @api.depends('date_assigned_first_time', 'date_closed')
    def _compute_duration(self):
        for rec in self:
            print ('yyyy', rec.date_assigned_first_time, rec.date_closed)
            rec.duration = rec._get_duration(rec.date_assigned_first_time, rec.date_closed)

    
    @pre_create('user_id')
    @pre_write('user_id')
    def _before_user_id_changed_by(self, changes):
        old_user, new_user = changes['user_id']
        print ('uuuu', old_user, new_user)
        if changes['user_id'].new_val and changes['user_id'].old_val:
            return {'date_assigned_first_time': self.date_assigned}
        elif changes['user_id'].new_val and not changes['user_id'].old_val:
            return {'date_assigned_first_time': fields.Datetime.now()}
        return {'date_assigned_first_time': False}


    @api.depends('date_moved', 'max_throughput_stage_time')
    def _get_request_state(self):
        for rec in self:
            rec.request_state = 'normal'
            if rec.date_moved and not rec.closed:
                computed_in_date = rec.date_moved + timedelta(hours=rec.max_throughput_stage_time)
                if computed_in_date.strftime('%m-%d-%Y') < datetime.today().strftime('%m-%d-%Y'):
                    rec.request_state = 'overdue'
                if computed_in_date.strftime('%m-%d-%Y') == datetime.today().strftime('%m-%d-%Y'):
                    rec.request_state = 'today'


    _sql_constraints = [
        ('name_uniq',
         'UNIQUE (name)',
         'Request name must be unique.'),
    ]
    #NEW - from old ims_helpdesk
    ticket_type = fields.Many2one(
        'formio.builder',
        'Ticket Type'
    )
    form_id = fields.Many2one(
        'formio.form',
        string="Form",
    )
    submission_instance = fields.Char(related='form_id.submission_instance', store=True)
    submission_email = fields.Char(related='form_id.submission_email')
    submission_company = fields.Char(related='form_id.submission_company')
    summary = fields.Char('Summary')

    def action_view_formio(self):
        form = self.env['formio.form'].search([('request_request_id','=',self.id)])
        return {
            "name": self.name,
            "type": "ir.actions.act_window",
            "res_model": "formio.form",
            "views": [(False, 'formio_form')],
            "view_mode": "formio_form",
            "target": "current",
            "res_id": form.id,
            "context": {}
        }

    @api.model
    def default_get(self, fields_list):
        res = super(RequestRequest, self).default_get(fields_list)

        path = http.request.httprequest.path if http.request else False
        if path and path.startswith('/web') or path == '/web':
            res.update({'channel_id': self.env.ref(
                'generic_request.request_channel_web').id})
        elif path and path.startswith('/xmlrpc') or path == '/xmlrpc':
            res.update({'channel_id': self.env.ref(
                'generic_request.request_channel_api').id})
        elif path and path.startswith('/jsonrpc') or path == '/jsonrpc':
            res.update({'channel_id': self.env.ref(
                'generic_request.request_channel_api').id})
        if 'parent_id' in fields_list:
            parent = self._context.get('generic_request_parent_id')
            res.update({'parent_id': parent})

        return res

    @api.depends('deadline_date', 'date_closed')
    def _compute_deadline_state(self):
        now = datetime.now().date()
        for rec in self:
            date_deadline = fields.Date.from_string(
                rec.deadline_date) if rec.deadline_date else False
            date_closed = fields.Date.from_string(
                rec.date_closed) if rec.date_closed else False
            if not date_deadline:
                rec.deadline_state = False
                continue

            if date_closed:
                if date_closed <= date_deadline:
                    rec.deadline_state = 'ok'
                else:
                    rec.deadline_state = 'overdue'
            else:
                if date_deadline > now:
                    rec.deadline_state = 'ok'
                elif date_deadline < now:
                    rec.deadline_state = 'overdue'
                elif date_deadline == now:
                    rec.deadline_state = 'today'

    @api.depends('stage_id', 'stage_id.type_id')
    def _compute_stage_colors(self):
        for rec in self:
            rec.stage_bg_color = rec.stage_id.res_bg_color
            rec.stage_label_color = rec.stage_id.res_label_color

    @api.depends('stage_id.route_out_ids.stage_to_id.closed')
    def _compute_can_be_closed(self):
        for record in self:
            record.can_be_closed = any((
                r.close for r in record.stage_id.route_out_ids))

    @api.depends('request_event_ids')
    def _compute_request_event_count(self):
        for record in self:
            record.request_event_count = len(record.request_event_ids)

    @api.depends()
    def _compute_is_new_request(self):
        for record in self:
            record.is_new_request = int(not bool(record.id))

    def _hook_can_change_request_text(self):
        self.ensure_one()
        return not self.closed

    def _hook_can_change_assignee(self):
        self.ensure_one()
        return not self.closed

    def _hook_can_change_category(self):
        self.ensure_one()
        return self.stage_id == self.type_id.sudo().start_stage_id

    def _hook_can_change_deadline(self):
        self.ensure_one()
        return not self.closed

    def _hook_can_change_author(self):
        self.ensure_one()
        return self.stage_id == self.type_id.sudo().start_stage_id

    @api.depends('type_id', 'stage_id', 'user_id',
                 'partner_id', 'created_by_id', 'category_id')
    def _compute_can_change_request_text(self):
        for rec in self:
            rec.can_change_request_text = rec._hook_can_change_request_text()

    @api.depends('type_id', 'stage_id', 'user_id',
                 'partner_id', 'created_by_id', 'category_id')
    def _compute_can_change_assignee(self):
        for rec in self:
            rec.can_change_assignee = rec._hook_can_change_assignee()

    @api.depends('type_id', 'type_id.start_stage_id', 'stage_id',
                 'user_id', 'partner_id', 'created_by_id', 'request_text',
                 'category_id')
    def _compute_can_change_author(self):
        for record in self:
            if not self.env.user.has_group(
                    'generic_request.group_request_user_can_change_author'):
                record.can_change_author = False
            else:
                record.can_change_author = record._hook_can_change_author()

    @api.depends('type_id', 'type_id.start_stage_id', 'stage_id')
    def _compute_can_change_category(self):
        for record in self:
            record.can_change_category = record._hook_can_change_category()

    @api.depends('type_id', 'type_id.start_stage_id', 'stage_id',
                 'deadline_date', 'category_id')
    def _compute_can_change_deadline(self):
        for record in self:
            record.can_change_deadline = record._hook_can_change_deadline()

    @api.depends('request_text')
    def _compute_request_text_sample(self):
        for request in self:
            text_list = html2text(request.request_text).splitlines()
            result = []
            while len(result) <= REQUEST_TEXT_SAMPLE_MAX_LINES and text_list:
                line = text_list.pop(0)
                line = line.lstrip('#').strip()
                if not line:
                    continue
                result.append(line)
            request.request_text_sample = "\n".join(result)

    @api.depends('user_id')
    def _compute_instruction_visible(self):
        for rec in self:
            rec.instruction_visible = (
                (
                    self.env.user == rec.user_id or
                    self.env.user.id == SUPERUSER_ID or
                    self.env.user.has_group(
                        'generic_request.group_request_manager')
                ) and (
                    rec.instruction_html and
                    rec.instruction_html != '<p><br></p>'
                )
            )

    @api.depends('type_id')
    def _compute_is_priority_complex(self):
        for rec in self:
            rec.is_priority_complex = rec.sudo().type_id.complex_priority

    @api.depends('_priority', 'impact', 'urgency')
    def _compute_priority(self):
        for rec in self:
            if rec.is_priority_complex:
                rec.priority = str(
                    PRIORITY_MAP[int(rec.impact)][int(rec.urgency)])
            else:
                rec.priority = rec._priority

    @api.depends('user_id')
    def _compute_is_assigned(self):
        for rec in self:
            rec.is_assigned = bool(rec.user_id)

    # When priority is complex, it is computed from impact and urgency
    # We do not need to write it directly from the field
    def _inverse_priority(self):
        for rec in self:
            if not rec.is_priority_complex:
                rec._priority = rec.priority

    @api.depends('author_id', 'partner_id')
    def _compute_related_a_p_request_ids(self):
        for record in self:
            # Usually this will be called on request form view and thus
            # computed only for one record. So, it will lead only to 4
            # search_counts per request to compute stat
            if record.id and record.author_id:
                record.update({
                    'author_related_request_open_count': self.search_count(
                        [('author_id', '=', record.author_id.id),
                         ('closed', '=', False),
                         ('id', '!=', record.id)]),
                    'author_related_request_closed_count': self.search_count(
                        [('author_id', '=', record.author_id.id),
                         ('closed', '=', True),
                         ('id', '!=', record.id)]),
                })
            else:
                record.update({
                    'author_related_request_open_count': 0,
                    'author_related_request_closed_count': 0,
                })

            if record.id and record.partner_id:
                record.update({
                    'partner_related_request_open_count': self.search_count(
                        [('partner_id', '=', record.partner_id.id),
                         ('closed', '=', False),
                         ('id', '!=', record.id)]),
                    'partner_related_request_closed_count': self.search_count(
                        [('partner_id', '=', record.partner_id.id),
                         ('closed', '=', True),
                         ('id', '!=', record.id)]),
                })
            else:
                record.update({
                    'partner_related_request_open_count': 0,
                    'partner_related_request_closed_count': 0,
                })

    @api.depends('timesheet_line_ids', 'timesheet_line_ids.amount',
                 'timesheet_planned_amount')
    def _compute_timesheet_line_data(self):
        for rec in self:
            timesheet_amount = 0.0
            for line in rec.timesheet_line_ids:
                timesheet_amount += line.amount
            rec.timesheet_amount = timesheet_amount

            if rec.timesheet_planned_amount:
                rec.timesheet_remaining_amount = (
                    rec.timesheet_planned_amount - timesheet_amount)
                rec.timesheet_progress = (
                    100.0 * (timesheet_amount / rec.timesheet_planned_amount))
            else:
                rec.timesheet_remaining_amount = 0.0
                rec.timesheet_progress = 0.0

    @api.depends('timesheet_line_ids', 'timesheet_line_ids.date_start',
                 'timesheet_line_ids.date_end')
    def _compute_timesheet_start_status(self):
        TimesheetLines = self.env['request.timesheet.line']
        domain = expression.AND([
            TimesheetLines._get_running_lines_domain(),
            [('request_id', 'in', self.ids)],
        ])
        grouped = self.env["request.timesheet.line"].read_group(
            domain=domain,
            fields=["id", 'request_id'],
            groupby=['request_id'],
        )
        lines_per_record = {
            group['request_id'][0]: group["request_id_count"]
            for group in grouped
        }

        for record in self:
            if lines_per_record.get(record.id, 0) > 0:
                record.timesheet_start_status = 'started'
            else:
                record.timesheet_start_status = 'not-started'

    @api.depends('stage_id')
    def _compute_stage_route_out_json(self):
        for rec in self:
            routes = []
            for route in rec.stage_id.route_out_ids:
                try:
                    route._ensure_can_move(rec)
                except exceptions.AccessError:  # pylint: disable=except-pass
                    # We have to ignore routes that cannot be used
                    # to move request
                    pass
                else:
                    # Add route to those allowed to move
                    if route.name:
                        route_name = route.name
                    else:
                        route_name = route.stage_to_id.name
                    routes += [{
                        'id': route.id,
                        'name': route_name,
                        'stage_to_id': route.stage_to_id.id,
                        'close': route.close,
                        'btn_style': route.button_style,
                    }]

            rec.stage_route_out_json = json.dumps({'routes': routes})

    @api.depends('child_ids')
    def _compute_child_count(self):
        for rec in self:
            rec.child_count = len(rec.child_ids)

    @api.constrains('parent_id')
    def _recursion_constraint(self):
        if not self._check_recursion():
            raise ValidationError(_(
                'Error! You cannot create recursive requests.'))

    def _create_update_from_type(self, r_type, vals):
        vals = dict(vals)
        # Name update
        if vals.get('name') == "###new###":
            # To set correct name for request generated from mail aliases
            # See code `mail.models.mail_thread.MailThread.message_new` - it
            # attempts to set name if it is empty. So we pass special name in
            # our method overload, and handle it here, to keep all request name
            # related logic in one place
            vals['name'] = False
        if not vals.get('name') and r_type.sequence_id:
            vals['name'] = r_type.sudo().sequence_id.next_by_id()
        elif not vals.get('name'):
            vals['name'] = self.env['ir.sequence'].sudo().next_by_code(
                'request.request.name')

        # Update stage
        if r_type.start_stage_id:
            vals['stage_id'] = r_type.start_stage_id.id
        else:
            raise exceptions.ValidationError(_(
                "Cannot create request of type '%(type_name)s':"
                " This type have no start stage defined!"
            ) % {'type_name': r_type.name})

        # Set default priority
        if r_type.sudo().complex_priority:
            if not vals.get('impact'):
                vals['impact'] = r_type.sudo().default_impact
            if not vals.get('urgency'):
                vals['urgency'] = r_type.sudo().default_urgency
        else:
            if not vals.get('priority'):
                vals['priority'] = r_type.sudo().default_priority

        return vals

    @api.model
    def _add_missing_default_values(self, values):
        if values.get('created_by_id') and 'author_id' not in values:
            # This is required to be present before super call, because
            # 'author_id' has it's own default value, and and unless it is set
            # explicitly, original default value (partner of current user)
            # will be used.
            create_user = self.env['res.users'].sudo().browse(
                values['created_by_id'])
            values = dict(
                values,
                author_id=create_user.partner_id.id)
        res = super(RequestRequest, self)._add_missing_default_values(values)

        if res.get('author_id') and 'partner_id' not in values:
            author = self.env['res.partner'].browse(res['author_id'])
            if author.commercial_partner_id != author:
                res['partner_id'] = author.commercial_partner_id.id
        return res

    def write(self, vals):
        if vals.get('stage_type_id'):
            if self.stage_type_id.code == 'assigned':
                if not vals.get('user_id') and not self.user_id:
                    raise ValidationError(_('Please Assign User'))
            # update remote ticket if available

        return super(RequestRequest, self).write(vals)

    def create_picking_from_request(self, pick_type):
        warehouse = self.env['stock.warehouse'].search([
            '&',
            ('type', '=', 'inventory'),
            ('wh_type', '=', 'central'),
            ('active', '=', True)
        ], limit=1)
        if warehouse:
            src_location = False
            dest_location = False
            picking_type = self.env['stock.picking.type'].sudo().search([
                ('code', '=', pick_type),
                ('warehouse_id', '=', warehouse.id),
                ('active', '=', True)], limit=1)
            if pick_type == 'outgoing':
                dest_location = self.env['stock.location'].sudo().search(
                    [('name', '=', 'Customers')], limit=1)
                src_location = picking_type.default_location_src_id
            if pick_type == 'incoming':
                src_location = self.env['stock.location'].sudo().search(
                    [('name', '=', 'Vendors')], limit=1)
                dest_location = picking_type.default_location_dest_id
            vals = {
                'picking_type_id': picking_type.id,
                'pick_type': pick_type,
                'company_id': self.env.user.company_id.id,
                'location_id': src_location.id or False,
                'location_dest_id': dest_location.id or False,
                'servicedesk_id': self.id
            }
            self.env['stock.picking'].sudo().create(vals)


    @api.model
    def create(self, vals):
        if vals.get('type_id', False):
            r_type = self.env['request.type'].browse(vals['type_id'])
            vals = self._create_update_from_type(r_type, vals)

        self_ctx = self.with_context(mail_create_nolog=False)
        existing_name = self.search([('name', '=', vals['name'])], limit=1)
        if existing_name:
            vals['name'] = vals['name'] + '-01'
        request = super(RequestRequest, self_ctx).create(vals)
        # create routines if required
        if request.auto_create_routine:
            code = request.auto_create_routine_code
            model = request.auto_create_routine_model_id.model
            routine_vals = {
                'site_id': request.auto_routine_site_id.id,
                'engineer_id': request.auto_routine_engineer_id.id,
                'servicedesk_id': request.id,
                'site_access': request.auto_routine_site_access,
                'work_order': request.auto_routine_site_wo,
                'schedule_date': request.deadline_date,
            }
            if model == 'dsk.asset.capture':
                if code == 'audit':
                    routine_vals['name'] = self.env['ir.sequence'].next_by_code('dsk.site.audit') or 'New Site Audit'
                    routine_vals['requirement'] = 'FAR'
                if code == 'deploy':
                    routine_vals['name'] = self.env['ir.sequence'].next_by_code('dsk.site.deploy') or 'New Site Deploy'
                    routine_vals['requirement'] = 'deploy'
                if code == 'decom':
                    routine_vals['name'] = self.env['ir.sequence'].next_by_code('dsk.site.decom') or 'New Site Decom'
                    routine_vals['requirement'] = 'site_decom'
            if model:
                model_obj = self.env[model]
                routine = model_obj.create(routine_vals)
        #set default assignee from type_id
        if request.type_id.default_assignee_id:
            AssignWizard = self.env['request.wizard.assign'].sudo()
            assign_wizard = AssignWizard.create({
                'user_id': request.type_id.default_assignee_id.id,
                'request_ids': [(6, 0, request.ids)],
                'comment': 'Ticket Auto Assigned',
            })
            assign_wizard.do_assign()

        # # auto create receiving order
        # if request.auto_create_receiving_request:
        #     request.create_picking_from_request('incoming')
        # if request.auto_create_shipping_request:
        #     request.create_picking_from_request('outgoing')

        if request.created_by_id.login == 'public':
            user = self.env['res.users'].search([('email', '=', request.submission_email)])
            if user:
                request.created_by_id = user.id
                request.author_id = user.partner_id.id
                if user.partner_id.commercial_partner_id != user.partner_id:
                    request.partner_id = user.partner_id.commercial_partner_id.id
                else:
                    request.partner_id = user.partner_id.id
        if request.type_id.code == 'mr':
            new_partners = self.env.company.mr_default_email_notify_ids.filtered(
                lambda x: x.company_id == self.env.user.msp_company_id or not x.company_id
            ).mapped('partner_id').ids
            new_partners = self.env.company.mr_default_email_notify_ids.mapped('partner_id').ids
            request.message_subscribe(new_partners)
        request.trigger_event('created')

        self_ctx = self.sudo()
        if self_ctx.env.context.get('generic_request_parent_id'):
            new_ctx = dict(self_ctx.env.context)
            new_ctx.pop('generic_request_parent_id')
            return request.with_env(request.env(context=new_ctx))
        # create local tickets if required
        # if request.create_local_ticket and request.local_ticket_instance_id:
        #     url = request.local_ticket_instance_id.instance_url + '/helpdesk/create_local_ticket'
        #     token = request.local_ticket_instance_id.get_access_token()
        #     # headers = {'content-type': 'application/x-www-form-urlencoded'}
        #     # resp = requests.post(url, data=data, headers=headers)
        #     headers = {
        #         'Authorization': 'Bearer %s' % token,
        #         'content-type': 'application/x-www-form-urlencoded'
        #     }
        #     data = request.read()[0]
        #     data['author_id_email'] = request.author_id.email
        #     data['created_by_id_email'] = request.created_by_id.email
        #     resp = requests.post(url, data=data, headers=headers)
        #     results = json.loads(resp.text)
        #     if 'code' not in results:
        #         request.remote_ticket_id = results['id']
        #         request.remote_ticket_link = results['remote_ticket_link']

        return request
    def _get_generic_tracking_fields(self):
        """ Compute list of fields that have to be tracked
        """
        # TODO: Do we need it? it seems that we have migrated most of code to
        # use pre/post_write decorators
        return super(
            RequestRequest, self
        )._get_generic_tracking_fields() | TRACK_FIELD_CHANGES

    @pre_write('active')
    def _before_active_changed(self, changes):
        if self.env.user.id == SUPERUSER_ID:
            return
        if not self.env.user.has_group(
                'generic_request.group_request_manager_can_archive_request'):
            raise exceptions.AccessError(_(
                "Operation change active is not allowed!"))

    @pre_write('type_id')
    def _before_type_id_changed(self, changes):
        raise exceptions.ValidationError(_(
            'It is not allowed to change request type'))

    @pre_create('user_id')
    @pre_write('user_id')
    def _before_user_id_changed(self, changes):
        if changes['user_id'].new_val:
            return {'date_assigned': fields.Datetime.now()}
        return {'date_assigned': False}

    @pre_write('stage_id')
    def _before_stage_id_changed(self, changes):
        Route = self.env['request.stage.route']
        old_stage, new_stage = changes['stage_id']
        route = False
        vals = {}
        if new_stage:
            max_throughput_stage_time = new_stage.max_throughput_time
            if self.priority:
                if self.priority == '0':
                    max_throughput_stage_time = new_stage.max_throughput_time
                else:
                    sla = new_stage.sla_ids.filtered(lambda r: r.priority == self.priority)
                    if sla:
                        max_throughput_stage_time = sla.max_throughput_time
                    else:
                        max_throughput_stage_time = new_stage.max_throughput_time
            sla_rule = new_stage.sla_ids.filtered(lambda r: r.priority == self.priority)
            if sla_rule:
                vals['escalate_user_id'] = sla_rule.escalate_user_id.id
            else:
                vals['escalate_user_id'] = new_stage.escalate_user_id.id
            # route = Route.ensure_route(self, new_stage.id)
            vals['last_route_id'] = False #route.id if route else False
            vals['date_moved'] = fields.Datetime.now()
            vals['stage_due_date'] = fields.Datetime.now() + timedelta(hours=max_throughput_stage_time)
            vals['moved_by_id'] = self.env.user.id
            vals['max_throughput_stage_time'] = max_throughput_stage_time
            vals['overdue_mail_sent'] = False
            vals['ticket_escalated'] = False

            if not old_stage.closed and new_stage.closed:
                vals['date_closed'] = fields.Datetime.now()
                vals['closed_by_id'] = self.env.user.id
            elif old_stage.closed and not new_stage.closed:
                vals['date_closed'] = False
                vals['closed_by_id'] = False
            elif new_stage.code == 'uat':
                vals['user_id'] = self.created_by_id.id
        else:
            vals['stage_id'] = old_stage.id
        return vals
    
    def cron_remind_violating_sla_ticket(self):
        # Get all tickets that already passed the max throughput time, sort by stage
        tickets = self.env['request.request'].search([
            ('ticket_escalated', '=', False),
            ('stage_id', '!=', False),
            ('stage_id.closed', '=', False),
            ('stage_due_date', '<', fields.Datetime.now())],
            order='stage_id')
        # Send email to each escalate_user_ids in each stage
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for ticket in tickets:
            url = "%s/web#id=%s&model=request.request&view_type=form" % (base_url, ticket.id)
            context = dict(self.env.context).copy()
            context.update({'url': url})
            sla_rule = ticket.stage_id.sla_ids.filtered(lambda r: r.priority == ticket.priority)
            print(sla_rule.escalate_user_id, ticket.stage_id.escalate_user_id)
            if not sla_rule.escalate_user_id and not ticket.stage_id.escalate_user_id:
                continue
            if sla_rule.escalate_user_id:
                user = sla_rule.escalate_user_id
            else:
                user = ticket.stage_id.escalate_user_id
            # Notify using chatbot
            self.notify_escalate_user(ticket)
            ticket.write({'ticket_escalated': True})

    def notify_escalate_user(self, record):
        print("NOTIFYING", record.name)
        if record and record.escalate_user_id:
            print("ESCALATE USER", record.escalate_user_id.name)
            esc_user = record.escalate_user_id
            odoobot_id = self.env['ir.model.data'].xmlid_to_res_id(
                "base.partner_root")
            channel = self.env['mail.channel'].sudo().with_context(
                mail_create_nosubscribe=True).create({
                'channel_partner_ids': [(4, esc_user.partner_id.id), (4, odoobot_id)],
                'public': 'private',
                'channel_type': 'chat',
                'email_send': False,
                'name': record.name
            })
            base_url = self.env['ir.config_parameter'].get_param('web.base.url')
            url = base_url + _(
                '/web#view_type=form&model=request.request&id=%d&active_id=%d'
                '&menu_id=') % (record.id, record.id)
            ticket_hyperlink = "<a href='%s'>%s</a>" % (url, record.name)
            message = """
            Dear %s, <br/>
            Please be informed that Ticket %s has exceeded the maximum allowed Stage time for Stage %s. <br/>
            Please take action immediately. <br/>
            NBot
            """ % (record.escalate_user_id.name, ticket_hyperlink, record.stage_id.name)
            recipient = [esc_user.partner_id.id, odoobot_id]
            record.message_post(body=message, subject=record.name)
            channel.sudo().message_post(body=message, author_id=odoobot_id,
                                        message_type="comment",
                                        subtype_xmlid="mail.mt_comment",
                                        partner_ids=recipient)
            print("SENT", record.name)

    @post_write('stage_id')
    def _after_stage_id_changed(self, changes):
        old_stage, new_stage = changes['stage_id']
        event_data = {
            'route_id': self.last_route_id.id,
            'old_stage_id': old_stage.id,
            'new_stage_id': new_stage.id,
        }
        if new_stage.closed and not old_stage.closed:
            self.trigger_event('closed', event_data)
        elif old_stage.closed and not new_stage.closed:
            self.trigger_event('reopened', event_data)
        elif new_stage.code == 'uat':
            self.trigger_event('uat', event_data)
            # assign ticket to creator for UAT
            AssignWizard = self.env['request.wizard.assign'].sudo()
            assign_wizard = AssignWizard.create({
                'user_id': self.created_by_id.id,
                'request_ids': [(6, 0, self.ids)],
                'comment': 'Ticket Assigned to Creator for UAT',
            })
            assign_wizard.do_assign()

        elif old_stage.code == 'uat-failed' and new_stage.code == 'qc':
            self.user_id = 8
        else:
            self.trigger_event('stage-changed', event_data)

    @post_write('user_id')
    def _after_user_id_changed(self, changes):
        old_user, new_user = changes['user_id']
        event_data = {
            'old_user_id': old_user.id,
            'new_user_id': new_user.id,
            'assign_comment': self.env.context.get('assign_comment', False)
        }
        if not old_user and new_user:
            self.trigger_event('assigned', event_data)
        elif old_user and new_user:
            self.trigger_event('reassigned', event_data)
        elif old_user and not new_user:
            self.trigger_event('unassigned', event_data)

    @post_write('request_text')
    def _after_request_text_changed(self, changes):
        self.trigger_event('changed', {
            'old_text': changes['request_text'][0],
            'new_text': changes['request_text'][1]})

    @post_write('category_id')
    def _after_category_id_changed(self, changes):
        self.trigger_event('category-changed', {
            'old_category_id': changes['category_id'][0].id,
            'new_category_id': changes['category_id'][1].id,
        })

    @post_write('author_id')
    def _after_author_id_changed(self, changes):
        self.trigger_event('author-changed', {
            'old_author_id': changes['author_id'][0].id,
            'new_author_id': changes['author_id'][1].id,
        })

    @post_write('partner_id')
    def _after_partner_id_changed(self, changes):
        self.trigger_event('partner-changed', {
            'old_partner_id': changes['partner_id'][0].id,
            'new_partner_id': changes['partner_id'][1].id,
        })

    @post_write('priority', 'impact', 'urgency')
    def _after_priority_changed(self, changes):
        if 'priority' in changes:
            self.trigger_event('priority-changed', {
                'old_priority': changes['priority'][0],
                'new_priority': changes['priority'][1]})
        if 'impact' in changes:
            old, new = changes['impact']
            old_priority = str(
                PRIORITY_MAP[int(old)][int(self.urgency)])
            new_priority = str(
                PRIORITY_MAP[int(new)][int(self.urgency)])
            self.trigger_event('priority-changed', {
                'old_priority': old_priority,
                'new_priority': new_priority})
            self.trigger_event('impact-changed', {
                'old_impact': old,
                'new_impact': new})
        if 'urgency' in changes:
            old, new = changes['urgency']
            old_priority = str(
                PRIORITY_MAP[int(self.impact)][int(old)])
            new_priority = str(
                PRIORITY_MAP[int(self.impact)][int(new)])
            self.trigger_event('priority-changed', {
                'old_priority': old_priority,
                'new_priority': new_priority})
            self.trigger_event('urgency-changed', {
                'old_urgency': old,
                'new_urgency': new})

    @post_write('deadline_date')
    def _after_deadline_changed(self, changes):
        self.trigger_event('deadline-changed', {
            'old_deadline': changes['deadline_date'][0],
            'new_deadline': changes['deadline_date'][1]})

    @post_write('kanban_state')
    def _after_kanban_state_changed(self, changes):
        self.trigger_event('kanban-state-changed', {
            'old_kanban_state': changes['kanban_state'][0],
            'new_kanban_state': changes['kanban_state'][1]})

    @post_write('active')
    def _after_active_changed(self, changes):
        __, new_active = changes['active']
        if new_active:
            event_code = 'request-unarchived'
        else:
            event_code = 'request-archived'
        self.trigger_event(event_code, {
            'request_active': event_code})

    def _creation_subtype(self):
        """ Determine mail subtype for request creation message/notification
        """
        return self.env.ref('generic_request.mt_request_created')

    @post_write('parent_id')
    def _after_parent_changed_trigger_request_event(self, changes):
        old, new = changes['parent_id']
        event_data = {
            'parent_old_id': old.id,
            'parent_new_id': new.id,
        }
        self.trigger_event('parent-request-changed', event_data)

    @post_write('stage_id')
    def _after_stage_id_changed_trigger_request_event(self, changes):
        old, new = changes['stage_id']
        parent_event_data = {
            'parent_route_id': self.last_route_id.id,
            'parent_old_stage_id': old.id,
            'parent_new_stage_id': new.id,
        }
        for child in self.child_ids:
            child.trigger_event(
                'parent-request-stage-changed', parent_event_data)
            if (not old.closed and new.closed):
                child.trigger_event(
                    'parent-request-closed', parent_event_data)

        if self.parent_id:
            subrequest_event_data = {
                'subrequest_id': self.id,
                'subrequest_old_stage_id': old.id,
                'subrequest_new_stage_id': new.id,
            }
            self.parent_id.trigger_event(
                'subrequest-stage-changed', subrequest_event_data)
            if (not old.closed and new.closed):
                self.parent_id.trigger_event(
                    'subrequest-closed', subrequest_event_data)

                # Here parent has at least one subrequest (self), so we do not
                # need to check if parent has subrequests.
                child_reqs = self.parent_id.sudo().child_ids
                if all(sr.stage_id.closed for sr in child_reqs):
                    self.parent_id.trigger_event(
                        'subrequest-all-subrequests-closed', {})

    def _track_subtype(self, init_values):
        """ Give the subtypes triggered by the changes on the record according
        to values that have been updated.

        :param init_values: the original values of the record;
                            only modified fields are present in the dict
        :type init_values: dict
        :returns: a subtype xml_id or False if no subtype is triggered
        """
        self.ensure_one()
        if 'stage_id' in init_values:
            init_stage = init_values['stage_id']
            if init_stage and init_stage != self.stage_id and \
                    self.stage_id.closed and not init_stage.closed:
                return self.env.ref('generic_request.mt_request_closed')
            if init_stage and init_stage != self.stage_id and \
                    not self.stage_id.closed and init_stage.closed:
                return self.env.ref('generic_request.mt_request_reopened')
            if init_stage != self.stage_id:
                return self.env.ref('generic_request.mt_request_stage_changed')

        return self.env.ref('generic_request.mt_request_updated')

    @api.onchange('type_id')
    def onchange_type_id(self):
        """ Set default stage_id
        """
        for request in self:
            if request.type_id and request.type_id.start_stage_id:
                request.stage_id = request.type_id.start_stage_id
            else:
                request.stage_id = self.env['request.stage'].browse([])

            # Set default priority
            if not request.is_priority_complex:
                request.priority = request.type_id.default_priority
            else:
                request.impact = request.type_id.default_impact
                request.urgency = request.type_id.default_urgency

            # Set default text for request
            if self.env.context.get('default_request_text'):
                continue
            if request.type_id and request.type_id.default_request_text:
                request.request_text = request.type_id.default_request_text

    @api.onchange('category_id', 'type_id', 'is_new_request')
    def _onchange_category_type(self):
        if self.type_id and self.category_id and self.is_new_request:
            # Clear type if it does not in allowed type for selected category
            # Or if request category is not selected
            if self.type_id not in self.category_id.request_type_ids:
                self.type_id = False

        res = {'domain': {}}
        domain = res['domain']
        if self.category_id:
            domain['type_id'] = [
                ('category_ids', '=', self.category_id.id),
                ('start_stage_id', '!=', False)]
        else:
            domain['type_id'] = [
                ('category_ids', '=', False),
                ('start_stage_id', '!=', False)]
        if not self.is_new_request:
            domain['category_id'] = [
                ('request_type_ids', '=', self.type_id.id)]
        else:
            domain['category_id'] = []
        return res

    @api.onchange('author_id')
    def _onchange_author_id(self):
        for rec in self:
            if rec.author_id:
                rec.partner_id = self.author_id.parent_id
            else:
                rec.partner_id = False

    @api.model
    def fields_view_get(self, view_id=None, view_type='form',
                        toolbar=False, submenu=False):
        params = self.env.context.get('params')
        result = super(RequestRequest, self).fields_view_get(
            view_id=view_id, view_type=view_type,
            toolbar=toolbar, submenu=submenu)

        # Make type_id and stage_id readonly for kanban mode.
        # this is required to disable kanban drag-and-drop features for this
        # fields, because changing request type or request stage in this way,
        # may lead to broken workflow for requests (no routes to move request
        # to next stage)
        if view_type == 'kanban':
            for rfield in KANBAN_READONLY_FIELDS:
                if rfield in result['fields']:
                    result['fields'][rfield]['readonly'] = True
        # if view_type == 'form':
        #     if params and params.get('id'):
        #         req_id = self.env['request.request'].browse(params.get('id'))
        #         print (req_id.type_code)
        #         if req_id:
        #             # tree = etree.fromstring(result['arch'])
        #             doc = etree.XML(result['arch'])
        #             for node in doc.xpath("//field[@name='stage_type_id'][@widget='statusbar']"):
        #                 if req_id.type_code == 'infinity-order':
        #                     domain = node.attrib['domain']
        #                     # node.attrib['domain'] = '[("is_market_place", "=", True)]'
        #                     node.set('domain', '[("is_market_place", "=", True)]')
        #                     result['arch'] = etree.tostring(doc, encoding='unicode')
                    

        return result

    def ensure_can_assign(self):
        for record in self:
            if not record.can_change_assignee:
                raise exceptions.UserError(_(
                    "You can not assign this (%(request)s) request"
                ) % {'request': record.display_name})

    def action_request_assign(self):
        self.ensure_can_assign()
        return self.env['generic.mixin.get.action'].get_action_by_xmlid(
            'generic_request.action_request_wizard_assign',
            context={'default_request_ids': [(6, 0, self.ids)]})

    def action_request_assign_to_me(self):
        self.ensure_can_assign()
        self.write({'user_id': self.env.user.id})

    # Default notifications
    def _send_default_notification__get_email_from(self, **kw):
        """ To be overloaded to change 'email_from' field for notifications
        """
        email_from = '"%s" <%s>' % (self.env.company.name, self.env.company.email)
        return email_from
        # return False

    def _send_default_notification__get_context(self, event):
        """ Compute context for default notification
        """
        values = event.get_context()
        values['company'] = self.env.user.company_id
        return values

    def _send_default_notification__get_msg_params(self, **kw):
        return dict(
            composition_mode='mass_mail',
            auto_delete=True,
            auto_delete_message=False,
            parent_id=False,  # override accidental context defaults
            subtype_id=self.env.ref('mail.mt_note').id,
            **kw,
        )

    def _send_default_notification__send(self, template, partners,
                                         event, **kw):
        """ Send default notification

            :param str template: XMLID of template to use for notification
            :param Recordset partners: List of partenrs that have to receive
                                       this notification
            :param Recordset event: Single record of 'request.event'
            :param function lazy_subject: function (self) that have to return
                                          translated string for subject
                                          for notification
        """
        values_g = self._send_default_notification__get_context(event)
        message_data_g = self._send_default_notification__get_msg_params(**kw)
        email_from = self._send_default_notification__get_email_from(**kw)
        if email_from:
            message_data_g['email_from'] = email_from

        # In order to handle translatable subjects, we use specific argument:
        # lazy_subject, which is function that receives 'self' and returns
        # string.
        lazy_subject = message_data_g.pop('lazy_subject', None)
        ks_cc_partner_ids = []
        if template in ['generic_request.message_request_created__author_mr', 'generic_request.message_request_fme_return_asset']:
            ks_cc_partner_ids = [(4, pid) for pid in
                                 self.env.company.mr_default_email_notify_ids.mapped('partner_id').ids]

        for partner in partners.sudo():
            # Skip partners without emails to avoid errors
            if not partner.email:
                continue
            values = dict(
                values_g,
                partner=partner,
            )
            self_ctx = self.sudo()

            # remove default author from context
            # This is required to fix bug in generic_request_crm:
            # when user create new request from lead, and there is default
            # author specified in context, then all notification messages use
            # that author as author of message. This way customer notification
            # has customer as author. Next block of code have to fix
            # this issue.
            if self_ctx.env.context.get('default_author_id'):
                new_ctx = dict(self_ctx.env.context)
                new_ctx.pop('default_author_id')
                self_ctx = self_ctx.with_env(self_ctx.env(context=new_ctx))

            if partner.lang:
                self_ctx = self_ctx.with_context(lang=partner.sudo().lang)
            message_data = dict(
                message_data_g,
                partner_ids=[(4, partner.id)],
                ks_cc_partner_ids=ks_cc_partner_ids,
                values=values)
            if lazy_subject:
                message_data['subject'] = lazy_subject(self_ctx)
            # self_ctx.message_post_with_view(
            #     template,
            #     **message_data)

    def _send_default_notification_created(self, event):
        template = 'generic_request.message_request_created__author'
        if not self.sudo().type_id.send_default_created_notification:
            return

        if self.type_id.code == 'mr':
            template = 'generic_request.message_request_created__author_mr'
        self._send_default_notification__send(
            template,
            self.sudo().author_id,
            event,
            lazy_subject=lambda self: _(
                "Request %(request)s successfully created!"
            ) % {'request': self.name},
        )

    def _send_default_notification_return_part(self, event):
        template = 'generic_request.message_request_fme_return_asset'
        if not self.sudo().type_id.send_default_created_notification:
            return
        ctx = self.env.context.copy()

        self.with_context(ctx)._send_default_notification__send(
            template,
            self.sudo().author_id,
            event,
            lazy_subject=lambda self: _(
                "Return for %(request)s successfully submitted!"
            ) % {'request': self.name},
        )

    def _send_default_notification_assigned(self, event):
        if not self.sudo().type_id.send_default_assigned_notification:
            return

        self._send_default_notification__send(
            'generic_request.message_request_assigned__assignee',
            event.sudo().new_user_id.partner_id,
            event,
            lazy_subject=lambda self: _(
                "You have been assigned to request %(request)s!"
            ) % {'request': self.name},
        )

    def _send_default_notification_uat(self, event):
        if not self.sudo().type_id.send_default_created_uat:
            return

        self._send_default_notification__send(
            'generic_request.message_request_assigned__uat',
            event.sudo().request_id.user_id.partner_id,
            event,
            lazy_subject=lambda self: _(
                "You have been assigned to request %(request)s! Please check once is it completed or not."
            ) % {'request': self.name},
        )


    def _send_default_notification_closed(self, event):
        if not self.sudo().type_id.send_default_closed_notification:
            return

        self._send_default_notification__send(
            'generic_request.message_request_closed__author',
            self.sudo().author_id,
            event,
            lazy_subject=lambda self: _(
                "Your request %(request)s has been closed!"
            ) % {'request': self.name},
        )

    def _send_default_notification_reopened(self, event):
        if not self.sudo().type_id.send_default_reopened_notification:
            return

        self._send_default_notification__send(
            'generic_request.message_request_reopened__author',
            self.sudo().author_id,
            event,
            lazy_subject=lambda self: _(
                "Your request %(request)s has been reopened!"
            ) % {'request': self.name},
        )

    def handle_request_event(self, event):
        """ Place to handle request events
        """
        if event.event_type_id.code in ('assigned', 'reassigned'):
            self._send_default_notification_assigned(event)
        elif event.event_type_id.code == 'created':
            self._send_default_notification_created(event)
        elif event.event_type_id.code == 'closed':
            self._send_default_notification_closed(event)
        elif event.event_type_id.code == 'reopened':
            self._send_default_notification_reopened(event)
        elif event.event_type_id.code == 'uat':
            self._send_default_notification_uat(event)
        elif event.event_type_id.code == 'uat_reminder':
            self._send_default_notification_uat_reminder(event)
        elif event.event_type_id.code == 'return_spare':
            self._send_default_notification_return_part(event)

    def trigger_event(self, event_type, event_data=None):
        """ Trigger an event.

            :param str event_type: code of event type
            :param dict event_data: dictionary with data to be written to event
        """
        event_type_id = self.env['request.event.type'].get_event_type_id(
            event_type)
        event_data = event_data if event_data is not None else {}
        user = self.env.user
        if not user:
            user = self.env['res.users'].sudo().browse(1)
        event_data.update({
            'event_type_id': event_type_id,
            'request_id': self.id,
            'user_id': user.id,
            'date': fields.Datetime.now(),
        })
        event = self.env['request.event'].sudo().create(event_data)
        self.handle_request_event(event)

    def get_mail_url(self):
        """ Get request URL to be used in mails
        """
        return "/mail/view/request/%s" % self.id

    def get_date_local(self, date):
        """ Get request URL to be used in mails
        """
        user_tz = self.env.user.tz or 'UTC'
        t = pytz.UTC.localize(date)
        local_date = t.astimezone(pytz.timezone(user_tz))
        return local_date.strftime("%d-%m-%Y %H:%M")

    def get_success_url(self):
        self.ensure_one()
        url = "%s/requests/pass/?id=%s" % (
                self.get_base_url(), self.id
            )
        return url

    def get_failed_url(self):
        self.ensure_one()
        url = "%s/requests/failed/?id=%s" % (
                self.get_base_url(), self.id
            )

        return url

    def _notify_get_groups(self, *args, **kwargs):
        """ Use custom url for *button_access* in notification emails
        """
        self.ensure_one()
        groups = super(RequestRequest, self)._notify_get_groups(
            *args, **kwargs)

        view_title = _('View Request')
        access_link = self.get_mail_url()

        # pylint: disable=unused-variable
        for group_name, group_method, group_data in groups:
            group_data['button_access'] = {
                'title': view_title,
                'url': access_link,
            }

        return groups

    def _message_auto_subscribe_followers(self, updated_values,
                                          default_subtype_ids):
        res = super(RequestRequest, self)._message_auto_subscribe_followers(
            updated_values, default_subtype_ids)

        if updated_values.get('author_id'):
            author = self.env['res.partner'].browse(
                updated_values['author_id'])
            if author.active:
                res.append((
                    author.id, default_subtype_ids, False))
        return res

    def _message_auto_subscribe_notify(self, partner_ids, template):
        # Disable sending mail to assigne, when request was assigned.
        # Custom notification will be sent, see _after_user_id_changed method
        # pylint: disable=useless-super-delegation
        return super(
            RequestRequest,
            self.with_context(mail_auto_subscribe_no_notify=True)
        )._message_auto_subscribe_notify(partner_ids, template)

    def _find_emails_from_msg(self, msg):
        """ Find emais from email message.
            Check 'to' and 'cc' fields

            :return: List of emails
        """
        # TODO: do we need to parse 'to' header here?
        return tools.email_split(
            (msg.get('to') or '') + ',' + (msg.get('cc') or ''))

    def _get_or_create_partner_from_email(self, email, force_create=False):
        """ This method will try to find partner by email.
            And if "force_create" is set to True, then it will try to create
            new partner (contact) for this email
        """
        partner_ids = self._mail_find_partner_from_emails(
            [email], force_create=force_create)
        if partner_ids:
            return partner_ids[0].id
        return False

    @api.model
    def _ensure_email_from_is_not_alias(self, msg_dict):
        """ Check that email is not come from alias.

            This needed to protect from infinite loops.
            If email come to odoo from alias managed by odoo,
            then it seems that there is going on something strage.
        """
        __, from_email = (
            self.env['res.partner']._parse_partner_name(msg_dict['from'])
            if msg_dict.get('from')
            else (False, False)
        )
        email_addr, email_domain = from_email.split('@')

        alias_domain = self.sudo().env["ir.config_parameter"].get_param(
            "mail.catchall.domain")
        if not alias_domain:
            # If alias domain is no configured, then assume that everything is
            # ok
            return
        if alias_domain.lower().strip() != email_domain.lower().strip():
            # If email come from different domain then everything seems to be
            # ok
            return

        check_domain = [
            ('alias_name', 'ilike', email_addr),
        ]
        if self.env['mail.alias'].search(check_domain, limit=1):
            raise ValueError(
                "Cannot create request from email sent from alias '%s'!\n"
                "Possible infinite loop, thus this email will be skipped!\n"
                "Subject: %s\n"
                "From: %s\n"
                "To: %s\n"
                "Message ID: %s" % (from_email,
                                    msg_dict.get('subject'),
                                    msg_dict.get('from'),
                                    msg_dict.get('to'),
                                    msg_dict.get('message_id')))

    def _validate_incoming_message(self, msg_dict):
        """ Validate incoming message, and if it is not acceptable,
            then raise error.

            This method could be overriden in third-party modules
            to provide extra validation options.
        """
        self._ensure_email_from_is_not_alias(msg_dict)

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """ Overrides mail_thread message_new that is called by the mailgateway
            through message_process.
            This override updates the document according to the email.
        """
        self._validate_incoming_message(msg_dict)
        company = self.env.user.company_id
        Partner = self.env['res.partner']
        defaults = dict(custom_values) if custom_values is not None else {}

        # Ensure we have message_id
        if not msg_dict.get('message_id'):
            msg_dict['message_id'] = self.env['mail.message']._get_message_id(
                msg_dict)

        # Compute default request text
        request_text = MAIL_REQUEST_TEXT_TMPL % {
            'subject': msg_dict.get('subject', _("No Subject")),
            'body': msg_dict.get('body', ''),
        }

        author_name, author_email = (
            Partner._parse_partner_name(msg_dict['from'])
            if msg_dict.get('from')
            else (False, False)
        )

        # Update defaults with partner and created_by_id if possible
        defaults.update({
            'name': "###new###",  # Spec name to avoid using subj as req name
            'request_text': request_text,
            'original_message_id': msg_dict['message_id'],
            'email_from': author_email,
            'email_cc': msg_dict.get('cc', ''),
        })
        author_id = msg_dict.get('author_id')

        # Create author from email if needed
        create_author = company.request_mail_create_author_contact_from_email
        if not author_id and create_author:
            author_id = self._get_or_create_partner_from_email(
                msg_dict['from'], force_create=True)
            if author_id:
                msg_dict['author_id'] = author_id

        if author_id:
            author = self.env['res.partner'].browse(author_id)
            defaults['author_id'] = author.id
            # TODO: May be we have to rely on autodetection of partner?
            #       (without explicitly setting it here)
            defaults['partner_id'] = author.commercial_partner_id.id
            if len(author.user_ids) == 1:
                defaults['created_by_id'] = author.user_ids[0].id
        else:
            author = False
            defaults['author_id'] = False
            defaults['partner_id'] = False
            defaults['author_name'] = author_name

        defaults.update({'channel_id': self.env.ref(
            'generic_request.request_channel_email').id})

        request = super(RequestRequest, self).message_new(
            msg_dict, custom_values=defaults)

        # Find partners from emails (cc) and subscribe them if needed
        partner_ids = request._mail_find_partner_from_emails(
            self._find_emails_from_msg(msg_dict),
            force_create=company.request_mail_create_cc_contact_from_email)
        partner_ids = [p.id for p in partner_ids if p]

        if author:
            request.message_subscribe([author.id])

        # Subscribe partners if needed
        if partner_ids and company.request_mail_auto_subscribe_cc_contacts:
            request.message_subscribe(partner_ids)
        return request

    def message_update(self, msg, update_vals=None):
        # Subscribe partners found in received email
        email_list = self._find_emails_from_msg(msg)
        company = self.env.user.company_id

        # contacts mentioned in cc
        partner_ids = self._mail_find_partner_from_emails(
            email_list,
            force_create=company.request_mail_create_cc_contact_from_email)
        partner_ids = [p.id for p in partner_ids if p]
        if partner_ids and company.request_mail_auto_subscribe_cc_contacts:
            self.message_subscribe(partner_ids)

        return super(RequestRequest, self).message_update(
            msg, update_vals=update_vals)

    def request_add_suggested_recipients(self, recipients):
        for record in self:
            if record.author_id:
                reason = _('Author')
                record._message_add_suggested_recipient(
                    recipients, partner=record.author_id, reason=reason)
            elif record.email_from:
                record._message_add_suggested_recipient(
                    recipients,
                    email="%s <%s>" % (record.author_name, record.email_from),
                    reason=_('Author Email'))
            if (record.email_cc and
                    self.env.user.company_id.request_mail_suggest_global_cc):
                for email in tools.email_split(record.email_cc):
                    record._message_add_suggested_recipient(
                        recipients, email=email,
                        reason=_('Global CC'))
            if (record.partner_id and
                    self.env.user.company_id.request_mail_suggest_partner):
                reason = _('Partner')
                record._message_add_suggested_recipient(
                    recipients, partner=record.partner_id, reason=reason)

    def _message_get_suggested_recipients(self):
        recipients = super(
            RequestRequest, self
        )._message_get_suggested_recipients()
        try:
            self.request_add_suggested_recipients(recipients)
        except exceptions.AcccessError:  # pylint: disable=except-pass
            pass
        return recipients

    def _message_post_after_hook(self, message, msg_vals, *args, **kwargs):
        # Overridden to add update request text with data from original message
        # This is required to make images display correctly,
        # because usualy, in emails, image's src looks liks:
        #     src="cid:ii_151b51a290ed6a91"
        if self and self.original_message_id == message.message_id:
            # We have to add this processing only in case when request is
            # created from email, and in this case, this method is called on
            # recordset with single record
            self.with_context(
                mail_notrack=True,
            ).write({
                'request_text': MAIL_REQUEST_TEXT_TMPL % {
                    'subject': message.subject,
                    'body': message.body,
                },
                'original_message_id': False,
            })

        return super(RequestRequest, self)._message_post_after_hook(
            message, msg_vals, *args, **kwargs
        )

    # def api_move_request(self, route_id, skip_sync=False):
    #     """ This method could be used to move request via specified route.
    #         In case of specified route is closing route, then it will return
    #         dictionary that describes action to open request's closing wizard.
    #
    #         :param int route_id: ID for request's route to move request.
    #     """
    #     self.ensure_one()
    #     route = self.env['request.stage.route'].browse(route_id)
    #     if route in self.stage_id.route_out_ids:
    #         # check if checklist is done
    #         not_done_checklist = self.checklist_ids.filtered(lambda x: x.route_id.id == route.id and not x.done)
    #         if len(not_done_checklist):
    #             raise UserError('Required Checklist is incomplete. Please complete the checklist before you can proceed.')
    #
    #         if route.close:
    #             return self.env[
    #                 'generic.mixin.get.action'
    #             ].get_action_by_xmlid(
    #                 'generic_request.action_request_wizard_close',
    #                 context={
    #                     'default_request_id': self.id,
    #                     'default_close_route_id': route_id,
    #                     'name_only': True,
    #                 })
    #         # self.stage_id = route.stage_to_id.id
    #         self.stage_type_id = self.env['request.stage.type'].search([('code', '=', route.stage_to_id.code)], limit=1).id
    #
    #         if self.remote_ticket_id and not skip_sync:
    #             request_id = self.remote_ticket_id
    #             remote_route_id = False
    #             local_route_id = False
    #             token = False
    #             if self.type_id.local_ticket_instance_id:
    #                 url = self.type_id.local_ticket_instance_id.instance_url + '/helpdesk/api_move_request'
    #                 token = self.type_id.local_ticket_instance_id.get_access_token()
    #                 remote_route_id = route_id
    #             else:
    #                 erp = self.env['nps.instance.connect'].search([('code', '=', 'erp')], limit=1)
    #                 if erp:
    #                     token = erp.get_access_token()
    #                     url = erp.instance_url + '/helpdesk/api_move_request'
    #                     local_route_id = route.remote_id
    #
    #             headers = {
    #                 'Authorization': 'Bearer %s' % token,
    #                 'content-type': 'application/x-www-form-urlencoded'
    #             }
    #             data = {
    #                 'request_id': request_id,
    #                 'remote_route_id': remote_route_id,
    #                 'route_id': local_route_id
    #             }
    #             if token:
    #                 resp = requests.post(url, data=data, headers=headers)
    #         return None
    #
    #     raise exceptions.UserError(_(
    #         "Cannot move request (%(request)s) by this route (%(route)s)"
    #     ) % {
    #         'request': self.name,
    #         'route': route.name,
    #     })

    def action_show_request_events(self):
        self.ensure_one()
        return self.env['generic.mixin.get.action'].get_action_by_xmlid(
            'generic_request.action_request_event_view',
            domain=[('request_id', '=', self.id)])

    def _request_timesheet_get_defaults(self):
        """ This method suppoesed to be overridden in other modules,
            to provide some additional default values for timesheet lines.
        """
        return {
            'request_id': self.id,
        }

    def action_close_request(self):
        self.ensure_one()
        return self.env['generic.mixin.get.action'].get_action_by_xmlid(
            'generic_request.action_request_wizard_close',
            context={
                'default_request_id': self.id,
                'name_only': True,
            })

    def action_start_work(self):
        self.ensure_one()
        TimesheetLines = self.env['request.timesheet.line']
        running_lines = TimesheetLines._find_running_lines()
        if running_lines:
            return self.env['generic.mixin.get.action'].get_action_by_xmlid(
                'generic_request.action_request_wizard_stop_work',
                context={
                    'default_timesheet_line_id': running_lines[0].id,
                    'request_timesheet_start_request_id': self.id,
                })

        data = self._request_timesheet_get_defaults()
        data['date_start'] = fields.Datetime.now()
        timesheet_line = TimesheetLines.create(data)
        self.trigger_event('timetracking-start-work', {
            'timesheet_line_id': timesheet_line.id,
        })
        return False

    def action_stop_work(self):
        self.ensure_one()
        TimesheetLines = self.env['request.timesheet.line']
        running_lines = TimesheetLines._find_running_lines()
        if running_lines:
            return self.env['generic.mixin.get.action'].get_action_by_xmlid(
                'generic_request.action_request_wizard_stop_work',
                context={'default_timesheet_line_id': running_lines[0].id})
        return False

    def action_request_view_timesheet_lines(self):
        self.ensure_one()
        return self.env['generic.mixin.get.action'].get_action_by_xmlid(
            'generic_request.action_timesheet_line',
            context={'default_request_id': self.id},
            domain=[('request_id', '=', self.id)],
        )

    def action_show_related_author_requests_closed(self):
        self.ensure_one()
        return self.env['generic.mixin.get.action'].get_action_by_xmlid(
            'generic_request.action_request_window',
            domain=[('author_id', '=', self.author_id.id),
                    ('id', '!=', self.id)],
            context={
                'search_default_filter_closed': 1,
            })

    def action_show_related_author_requests_opened(self):
        self.ensure_one()
        return self.env['generic.mixin.get.action'].get_action_by_xmlid(
            'generic_request.action_request_window',
            domain=[('author_id', '=', self.author_id.id),
                    ('id', '!=', self.id)],
            context={
                'search_default_filter_open': 1,
            })

    def action_show_related_partner_requests_closed(self):
        self.ensure_one()
        return self.env['generic.mixin.get.action'].get_action_by_xmlid(
            'generic_request.action_request_window',
            domain=[('partner_id', '=', self.partner_id.id),
                    ('id', '!=', self.id)],
            context={
                'search_default_filter_closed': 1,
            })

    def action_show_related_partner_requests_opened(self):
        self.ensure_one()
        return self.env['generic.mixin.get.action'].get_action_by_xmlid(
            'generic_request.action_request_window',
            domain=[('partner_id', '=', self.partner_id.id),
                    ('id', '!=', self.id)],
            context={
                'search_default_filter_open': 1,
            })

    def action_open_parent(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "request.request",
            "name": "Parent Request",
            "view_mode": "form",
            "target": "new",
            "res_id": self.parent_id.id
        }

    def action_button_show_subrequests(self):
        action = self.get_action_by_xmlid(
            'generic_request.action_request_window',
            context={'generic_request_parent_id': self.id,
                     'search_default_filter_open': True},
            domain=[('parent_id', '=', self.id)],
        )
        action.update({
            'name': _('Subrequests'),
            'display_name': _('Subrequests'),
        })
        return action

    def remove_attachment_details_from_ticket_description(self):
        for this in self:
            try:
                str = this.request_text
                substring1 = str.split('<tr><th>attachment</th><td>')[0]
                substring2 = '<tr><th>attachment</th><td> For attachments please click the Paperclip below </td></tr>'
                substring3 = str.split('<tr><th>form</th><td></td></tr></tbody></table>')[1]
                substring4 = substring3.split('</table></td></tr>')[1]
                complete_str = substring1 + substring2 + substring4
                this.request_text = complete_str
            except Exception as e:

                _logger.exception("Failed to remove attachment table from "
                                  "description: Ticket: %s" % this.name)

    def send_overdue_mail(self, record=None):
        if record:
            url = "%s/web#id=%s&model=request.request&view_type=form" % (
                self.get_base_url(),
                record.id
            )
            context = dict(self.env.context).copy()
            context.update({'url': url})
            template = self.env.ref(
                'generic_request.email_template_request_overdue')
            template.with_context(context).send_mail(record.id, force_send=True)
            return True
        return False


    @api.model
    def _scheduler_overdue(self):
        request_overdue = self.env['request.request'].sudo().search([('request_state', '=', 'overdue'), ('overdue_mail_sent', '=', False), ('closed', '=', False)])
        for req in request_overdue:
            print (req, req.name)
            if req.send_overdue_mail(req):
                req.overdue_mail_sent = True
            
            
        

    @api.model
    def _scheduler_migration(self, days=False):
        """ Run migration for helpdesk requests.
        """
        
        # tickets = self.env['helpdesk.request'].sudo().search(
        #     [('create_date', '<', '2022-07-26 09:38:00.77258')],
        # )
        # print (len(tickets))
        request_tickets = self.env['request.request'].sudo().search([('form_id', '=', False)])
        ticket_no = 0
        request_no_exist = 0
        request_does_not_exist = 0
        for ticket in self.env['helpdesk.request'].sudo().search([]):
            ticket_no += 1
            if ticket.form_id:
                request = self.env['request.request'].search([('form_id', '=', ticket.form_id.id)])
                if request.stage_id.closed != request.closed:
                    request.closed = request.stage_id.closed
                if ticket.form_id.request_request_id:
                    request_no_exist += 1
                else:
                    request_does_not_exist += 1
                    schema_data = json.loads(ticket.form_id.builder_id.schema)
                    submission_data = ticket.form_id.submission_data
                    submission_dict = json.loads(ticket.form_id.submission_data)
                    submission_dict.pop('submit')
                    name = ''
                    if 'summary' in submission_dict:
                        name = submission_dict['summary']
                    submission_dict_new = {}
                    stage_type_id = False
                    if 'summary' in submission_dict:
                        name = submission_dict['summary']
                    if 'files' in submission_dict:
                        submission_dict.pop('files')
                    if 'upload' in submission_dict:
                        submission_dict.pop('upload')
                    if 'attachment' in submission_dict:
                        submission_dict.pop('attachment')
                    if 'cancel' in submission_dict:
                        submission_dict.pop('cancel')
                    default_user_id = False
                    if ticket.form_id.default_user_id:
                        default_user_id = ticket.form_id.default_user_id.id
                    for submit_key, submit_value in submission_dict.items():
                        for key, value in schema_data.items():
                            for v in value:
                                if v.get('key') and v.get('key') == submit_key:
                                    submission_dict_new[v.get('label')] = submit_value
                                    # submission_dict[v.get('label')] = submission_dict.pop(submit_key)
                    submission_data = json.dumps(submission_dict_new)
                    #convert json to html and add to 'request_text'
                    

                    submission_table = json2html.convert(
                        json=submission_data,
                        table_attributes="id=\"info-table\" class=\"table table-striped table-bordered\""
                    )
                    if ticket.assign_to:
                        default_user_id = ticket.assign_to.id
                    if not ticket.assign_to and ticket.user_id:
                        default_user_id = ticket.user_id.id

                    if ticket.state == 'support':
                        stage_type_id = self.env['request.stage.type'].search([('code', '=', 'in-progress')], limit=1).id
                        stage_id = self.env['request.stage'].search([('code', '=', 'in-progress'), ('request_type_id', '=', ticket.form_id.builder_id.request_type_id.id)]).id
                        closed = self.env['request.stage'].search([('code', '=', 'in-progress'), ('request_type_id', '=', ticket.form_id.builder_id.request_type_id.id)]).closed
                    elif ticket.state in ('hdo', 'draft'):
                        stage_type_id = self.env['request.stage.type'].search([('code', '=', 'new')]).id
                        stage_id = self.env['request.stage'].search([('code', '=', 'new'), ('request_type_id', '=', ticket.form_id.builder_id.request_type_id.id)]).id
                        closed = self.env['request.stage'].search([('code', '=', 'new'), ('request_type_id', '=', ticket.form_id.builder_id.request_type_id.id)]).closed
                    elif ticket.state == 'resolved':
                        stage_type_id = self.env['request.stage.type'].search([('code', '=', 'close')]).id
                        stage_id = self.env['request.stage'].search([('code', '=', 'close'), ('request_type_id', '=', ticket.form_id.builder_id.request_type_id.id)]).id
                        closed = self.env['request.stage'].search([('code', '=', 'close'), ('request_type_id', '=', ticket.form_id.builder_id.request_type_id.id)]).closed
                    if ticket.priority == '1':
                        priority = '2'
                    elif ticket.priority == '2':
                        priority = '3'
                    elif ticket.priority == '3':
                        priority = '4'

                    
                    body = {
                        'created_by_id': ticket.form_id.submission_user_id.id,
                        'moved_by_id': ticket.user_id and ticket.user_id.id,
                        'closed_by_id': ticket.user_id and ticket.user_id.id,
                        'summary': name,
                        'ticket_type': ticket.form_id.builder_id.id,
                        'form_id': ticket.form_id.id,
                        'type_id': ticket.form_id.request_type_id.id,
                        'category_id': ticket.form_id.request_category_id.id,
                        'request_text': submission_table,
                        'user_id': default_user_id,
                        'priority': priority,
                        'jira_url': ticket.jira_url,
                        'asana_url': ticket.asana_url,
                        'closed': closed


                    }
                    
                    res = self.env['request.request'].create(body)
                    if ticket.assigned_date:
                        date_assigned = ticket.assigned_date.astimezone(UTC).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                        date_moved = ticket.assigned_date.astimezone(UTC).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                    else:
                        date_assigned = None
                        date_moved = None
                    
                    if ticket.closed_date:
                        date_closed = ticket.closed_date.astimezone(UTC).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                    else:
                        date_closed = None
                    date_created = ticket.create_date.astimezone(UTC).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                    # create_date = ticket.create_date.astimezone(UTC).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                    # write_date = ticket.write_date.astimezone(UTC).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                    create_uid = ticket.create_uid.id
                    write_uid = ticket.write_uid.id
                    
                    query = """
                            UPDATE request_request
                                SET stage_type_id = %s, stage_id = %s, date_assigned = %s, date_closed = %s, date_moved = %s, date_created= %s, create_uid = %s, write_uid = %s
                            WHERE id = %s
                        """
                    print ('kk', query)
                    self.env.cr.execute(query, (stage_type_id, stage_id, date_assigned, date_closed, date_moved, date_created, create_uid, write_uid, res.id))
                    
                    
                    ticket.form_id.request_request_id = res.id
                    


            else:
                pass

        print ('helpdeks total ticket', ticket_no)
        print ('request total ticket already exist', request_no_exist)
        print ('request total ticket does not exist', request_does_not_exist)
        return True

    def _send_default_notification_uat_reminder(self, event):
        if not self.sudo().type_id.send_default_created_uat:
            return

        self._send_default_notification__send(
            'generic_request.message_request_assigned__uat',
            event.sudo().request_id.user_id.partner_id,
            event,
            lazy_subject=lambda self: _(
                "You have been assigned to request %(request)s! Please check once is it completed or not."
            ) % {'request': self.name},
        )

    @api.model
    def cron_remind_user_uat_tickets(self):
        for this in self.search([]):
            if this.stage_id.code == 'uat':
                event_data = {
                    'old_user_id': this.user_id.id,
                    'new_user_id': this.user_id.id,
                }
                this.trigger_event('uat_reminder', event_data)
