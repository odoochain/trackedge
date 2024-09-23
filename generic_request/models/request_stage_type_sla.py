from odoo import models, fields, api, _
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


class RequestStageTypeSLA(models.Model):
    _name = 'request.stage.type.sla'
    _description = 'Request Stage Type SLA'

    stage_type_id = fields.Many2one('request.stage.type', string='Stage Type')
    stage_id = fields.Many2one('request.stage', string='Stage')
    priority = fields.Selection(selection=AVAILABLE_PRIORITIES, string='Ticket Priority', help="Priority of request")
    escalate_user_id = fields.Many2one('res.users', string='Escalate User')
    max_throughput_time = fields.Float('Max Throughput Time(Hrs)', default=24.0)
