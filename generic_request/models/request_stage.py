import json
import logging
import requests
from odoo import models, fields, api, exceptions, _


DEFAULT_BG_COLOR = 'rgba(120,120,120,1)'
DEFAULT_LABEL_COLOR = 'rgba(255,255,255,1)'


class RequestStage(models.Model):
    _name = "request.stage"
    _inherit = [
        'generic.mixin.name_with_code',
        'generic.mixin.track.changes',
    ]
    _description = "Request Stage"
    _order = "sequence"

    # Defined in generic.mixin.name_with_code
    name = fields.Char()
    code = fields.Char()

    type_id = fields.Many2one(
        'request.stage.type', string="Stage Type", index=True,
        ondelete="restrict")
    active = fields.Boolean(
        default=True, index=True)

    sequence = fields.Integer(default=5, index=True)
    request_type_id = fields.Many2one(
        'request.type', 'Request Type', ondelete='cascade',
        required=True, index=True)
    description = fields.Text(translate=True)
    help_html = fields.Html("Help", translate=True)
    bg_color = fields.Char(default=DEFAULT_BG_COLOR, string="Backgroung Color")
    label_color = fields.Char(default=DEFAULT_LABEL_COLOR)

    # Custom colors
    use_custom_colors = fields.Boolean(
        help="Select colors from the palette manually")
    res_bg_color = fields.Char(
        compute='_compute_custom_colors', readonly=True,
        string="Backgroung Color")
    res_label_color = fields.Char(
        compute='_compute_custom_colors',
        readonly=True, string="Label Color")

    # Route relations
    route_in_ids = fields.One2many(
        'request.stage.route', 'stage_to_id', 'Incoming routes')
    route_in_count = fields.Integer(
        'Routes In', compute='_compute_routes_in_count', readonly=True)
    route_out_ids = fields.One2many(
        'request.stage.route', 'stage_from_id', 'Outgoing routes')
    route_out_count = fields.Integer(
        'Routes Out', compute='_compute_routes_out_count', readonly=True)

    previous_stage_ids = fields.Many2many(
        'request.stage', 'request_stage_prev_stage_ids_rel',
        'stage_id', 'prev_stage_id',
        string='Previous stages', compute='_compute_previous_stage_ids',
        store=True)
    closed = fields.Boolean(
        index=True, help="Is request on this stage closed?")
    max_throughput_time = fields.Float('Max Throughput Time(Hrs)', default=24.0)
    remote_id = fields.Integer()
    sla_ids = fields.One2many('request.stage.type.sla', 'stage_id', string='SLA', default=lambda self: self._default_sla_ids())
    escalate_user_id = fields.Many2one('res.users', string='Escalate User')

    _sql_constraints = [
        ('stage_name_uniq',
         'UNIQUE (request_type_id, name)',
         'Stage name must be uniq for request type'),
        ('stage_code_uniq',
         'UNIQUE (request_type_id, code)',
         'Stage code must be uniq for request type'),
    ]

    @api.model
    def _default_sla_ids(self):
        return [
            (0, 0, {
                'priority': '1',
                'max_throughput_time': 24.0,
            }),
            (0, 0, {
                'priority': '2',
                'max_throughput_time': 24.0,
            }),
            (0, 0, {
                'priority': '3',
                'max_throughput_time': 24.0,
            }),
            (0, 0, {
                'priority': '4',
                'max_throughput_time': 24.0,
            }),
        ]
    
    def quick_create_sla(self):
        self.sla_ids = self._default_sla_ids()

    @api.depends('request_type_id', 'request_type_id.stage_ids',
                 'request_type_id.route_ids',
                 'request_type_id.route_ids.stage_from_id',
                 'request_type_id.route_ids.stage_to_id')
    def _compute_previous_stage_ids(self):
        for stage in self:
            route_ids = stage.request_type_id.route_ids.filtered(
                lambda r: r.stage_to_id == stage)

            stage_ids = route_ids.mapped('stage_from_id')
            stage.previous_stage_ids = stage_ids

    @api.depends('route_in_ids')
    def _compute_routes_in_count(self):
        for record in self:
            record.route_in_count = len(record.route_in_ids)

    @api.depends('route_out_ids')
    def _compute_routes_out_count(self):
        for record in self:
            record.route_out_count = len(record.route_out_ids)

    @api.onchange('type_id')
    def onchange_type_id(self):
        for stage in self:
            stage.code = stage.type_id.code
            stage.max_throughput_time = stage.type_id.max_throughput_time

    @api.depends('bg_color', 'label_color', 'type_id', 'use_custom_colors')
    def _compute_custom_colors(self):
        for rec in self:
            if rec.use_custom_colors:
                rec.res_bg_color = rec.bg_color
                rec.res_label_color = rec.label_color
            elif rec.type_id:
                rec.res_bg_color = rec.type_id.bg_color
                rec.res_label_color = rec.type_id.label_color
            else:
                rec.res_bg_color = DEFAULT_BG_COLOR
                rec.res_label_color = DEFAULT_LABEL_COLOR

    @api.model
    def _add_missing_default_values(self, values):
        res = super(RequestStage, self)._add_missing_default_values(values)
        if 'sequence' not in values and res.get('request_type_id'):
            stages = self.search(
                [('request_type_id', '=', res['request_type_id'])])
            if stages:
                res['sequence'] = max(s.sequence for s in stages) + 1
        return res

    def action_show_incoming_routes(self):
        self.ensure_one()
        return self.env['generic.mixin.get.action'].get_action_by_xmlid(
            'generic_request.action_request_stage_incoming_routes',
            context={
                'default_stage_to_id': self.id,
                'default_request_type_id': self.request_type_id.id,
            })

    def action_show_outgoing_routes(self):
        self.ensure_one()
        return self.env['generic.mixin.get.action'].get_action_by_xmlid(
            'generic_request.action_request_stage_outgoing_routes',
            context={
                'default_stage_from_id': self.id,
                'default_request_type_id': self.request_type_id.id,
            })

    def write(self, vals):
        ret = super(RequestStage, self).write(vals)
        if 'code' in vals or 'type_id' in vals:
            self.request_type_id.request_ids.compute_request_stage_ids()
        return ret
    @api.model
    def create(self, vals):
        ret = super(RequestStage, self).create(vals)
        if 'code' in vals or 'type_id' in vals:
            self.request_type_id.request_ids.compute_request_stage_ids()
        return ret

    def unlink(self):
        messages = []
        for record in self:
            if record.route_out_ids or record.route_in_ids:
                routes = "\n".join(
                    ["- %s" % r.display_name for r in record.route_in_ids] +
                    ["- %s" % r.display_name for r in record.route_out_ids])
                msg = _(
                    "Cannot delete stage %(stage_name)s because it is "
                    "referenced from following routes:\n%(routes)s"
                ) % {
                    'stage_name': record.display_name,
                    'routes': routes,
                }
                messages += [msg]
        if messages:
            raise exceptions.ValidationError("\n\n".join(messages))
        return super(RequestStage, self).unlink()

    @api.model
    def cron_sync_request_stage(self):
        erp = self.env['nps.instance.connect'].search([('code', '=', 'erp')], limit=1)
        token = erp.get_access_token()
        api_url = erp.instance_url + '/api/search_read/request.stage?limit=1000'
        headers = {
            'Authorization': 'Bearer %s' % token
        }
        response = requests.get(api_url, headers=headers)
        convertedDict = json.loads(response.text)
        for line in convertedDict:
            existing_record = self.search([('remote_id', '=', line['id'])], limit=1)
            request_type_id = False
            type_id = False
            if line['request_type_id']:
                type = self.env['request.type'].search([('remote_id', '=', line['request_type_id'][0])], limit=1)
                if type:
                    request_type_id = type.id
            if line['type_id']:
                stage_type = self.env['request.stage.type'].search([('remote_id', '=', line['type_id'][0])], limit=1)
                if stage_type:
                    type_id = stage_type.id
            vals = {
                'remote_id': line['id'],
                'name': line['name'],
                'active': line['active'],
                'max_throughput_time': line['max_throughput_time'],
                'code': line['code'],
                'request_type_id': request_type_id,
                'type_id': type_id,
                'closed': line['closed'],
                'use_custom_colors': line['use_custom_colors'],
                'res_bg_color': line['res_bg_color'],
                'res_label_color': line['res_label_color'],
                'help_html': line['help_html'],
                'description': line['description']
            }
            if not existing_record:
                try:
                    new_record = self.create(vals)
                except Exception as e:  # pylint: disable=except-pass
                    self.env.cr.rollback()
                    continue
                else:
                    pass
            else:
                existing_record.write(vals)
        self.env['request.type'].cron_sync_request_type()
