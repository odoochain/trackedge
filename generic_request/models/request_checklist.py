
from odoo import models, fields, api, exceptions, _


class RequestRequest(models.Model):
    _inherit = 'request.request'

    checklist_ids = fields.One2many('request.checklist', 'request_id',
        domain=lambda self: [('stage_from_id', '=', self.stage_id.id)])

    def update_checklists(self):
        for route in self.type_id.route_ids:
            for checklist in route.checklist_ids:
                vals = {
                    'origin_checklist_id': checklist.id,
                    'request_id': self.id,
                    'name': checklist.name,
                    'route_id': route.id
                }
                existing = self.checklist_ids.filtered(lambda x: x.origin_checklist_id.id == checklist.id)
                if existing:
                    existing.write(vals)
                else:
                    self.env["request.checklist"].create(vals)

    @api.model
    def create(self, vals):
        ret = super(RequestRequest, self).create(vals)
        ret.update_checklists()
        return ret


class RequestChecklist(models.Model):
    _name = "request.checklist"
    _description = "Request Checklist"

    origin_checklist_id = fields.Many2one('request.stage.route.checklist')
    request_id = fields.Many2one("request.request")
    name = fields.Char(required=True)
    done = fields.Boolean()
    route_id = fields.Many2one("request.stage.route")
    stage_from_id = fields.Many2one('request.stage', related='route_id.stage_from_id')
    stage_to_id = fields.Many2one('request.stage', related='route_id.stage_to_id')
