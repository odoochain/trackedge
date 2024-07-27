
from odoo import models, fields


class RequestStageRouteChecklist(models.Model):
    _name = "request.stage.route.checklist"
    _description = "Request Stage Route Checklist"

    name = fields.Char(required=True)
    done = fields.Boolean()
    route_id = fields.Many2one("request.stage.route")
    stage_from_id = fields.Many2one('request.stage', related='route_id.stage_from_id')
    stage_to_id = fields.Many2one('request.stage', related='route_id.stage_to_id')
