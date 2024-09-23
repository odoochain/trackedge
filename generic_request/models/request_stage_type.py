import json
import logging
import requests
from odoo import models, fields, api
from .request_stage import DEFAULT_BG_COLOR, DEFAULT_LABEL_COLOR


class RequestStageType(models.Model):
    _name = 'request.stage.type'
    _inherit = [
        'generic.mixin.name_with_code',
        'generic.mixin.uniq_name_code',
        'generic.mixin.track.changes',
    ]
    _description = 'Request Stage Type'
    _order = "sequence"

    # Defined in generic.mixin.name_with_code
    name = fields.Char()
    code = fields.Char()

    active = fields.Boolean(index=True, default=True)
    sequence = fields.Integer(default=5, index=True)
    bg_color = fields.Char(default=DEFAULT_BG_COLOR, string="Backgroung Color")
    label_color = fields.Char(default=DEFAULT_LABEL_COLOR)
    request_ids = fields.One2many('request.request', 'stage_type_id')
    request_count = fields.Integer(
        compute='_compute_request_count', readonly=True)
    max_throughput_time = fields.Float('Max Throughput Time(Hrs)', default=24.0)
    sla_ids = fields.One2many('request.stage.type.sla', 'stage_type_id', string='SLA', default=lambda self: self._default_sla_ids())
    is_market_place = fields.Boolean('Is Marketplace Stage?')
    remote_id = fields.Integer()

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

    @api.depends('request_ids')
    def _compute_request_count(self):
        for rec in self:
            rec.request_count = len(rec.request_ids)

    def action_show_requests(self):
        self.ensure_one()
        return self.env['generic.mixin.get.action'].get_action_by_xmlid(
            'generic_request.action_request_window',
            context={'default_stage_type_id': self.id},
            domain=[('stage_type_id', '=', self.id)])

    @api.model
    def cron_sync_request_stage_type(self):
        erp = self.env['nps.instance.connect'].search([('code', '=', 'erp')], limit=1)
        token = erp.get_access_token()
        api_url = erp.instance_url + '/api/search_read/request.stage.type?limit=1000'
        headers = {
            'Authorization': 'Bearer %s' % token
        }
        response = requests.get(api_url, headers=headers)
        convertedDict = json.loads(response.text)
        for line in convertedDict:
            existing_record = self.search([('remote_id', '=', line['id'])], limit=1)
            vals = {
                'remote_id': line['id'],
                'name': line['name'],
                'active': line['active'],
                'max_throughput_time': line['max_throughput_time'],
                'code': line['code'],
                'is_market_place': line['is_market_place'],
                'bg_color': line['bg_color'],
                'label_color': line['label_color'],
            }
            if not existing_record:
                new_record = self.create(vals)
            else:
                existing_record.write(vals)