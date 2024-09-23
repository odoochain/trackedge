import json
import logging
from urllib import response
from odoo.tools.safe_eval import safe_eval
from odoo import _, http, release
from odoo.http import request, Response
_logger = logging.getLogger(__name__)

# from odoo.addons.muk_rest import validators, tools
# from odoo.addons.muk_rest.tools.common import parse_value
# from odoo.addons.muk_utils.tools.json import ResponseEncoder, RecordEncoder


class NPSHelpdeskAPI(http.Controller):

    @http.route(['/helpdesk/create_local_ticket'],
        auth="none", type='http', methods=['POST'], csrf=False)
        # URL/helpdesk/create_local_ticket?values=vals
        # vals = {'name':'name'}
    def create_local_ticket(self, **kw):
        type_id = False
        kind_id = False
        category_id = False
        partner_id = False
        author_id = False
        created_by_id = False
        for x in kw:
            if kw[x] == 'False':
                kw[x] = False
            if kw[x] == 'True':
                kw[x] = True
        type =  request.env['request.type'].sudo().search(
            [('remote_id', '=', kw['type_id'])], limit=1)
        if type:
            type_id = type.id
        category = request.env['request.category'].sudo().search(
            [('remote_id', '=', kw['category_id'])], limit=1)
        if category:
            category_id = category.id
        author = request.env['res.partner'].sudo().search(
            [('email', '=', kw['author_id_email'])], limit=1)
        if author:
            author_id = author.id
        creator = request.env['res.users'].sudo().search(
            [('email', '=', kw['created_by_id_email'])], limit=1)
        if creator:
            created_by_id = creator.id
        create_vals = {
            'remote_ticket_id': kw['id'],
            'name': kw['name'],
            'help_html': kw['help_html'],
            'category_help_html': kw['category_help_html'],
            'stage_help_html': kw['stage_help_html'],
            'instruction_html': kw['instruction_html'],
            'note_html': kw['note_html'],
            '_priority': kw['_priority'],
            'priority': kw['priority'],
            'impact': kw['impact'],
            'urgency': kw['urgency'],
            'is_priority_complex': kw['is_priority_complex'],
            'request_text': kw['request_text'],
            'request_text_sample': kw['request_text_sample'],
            'deadline_date': kw['deadline_date'],
            'request_state': kw['request_state'],
            'remote_ticket_link': kw['ticket_link'],
            'is_market_place_request': kw['is_market_place_request'],
            'submission_instance': kw['submission_instance'],
            'submission_email': kw['submission_email'],
            'submission_company': kw['submission_company'],
            'summary': kw['summary'],
            'type_id': type_id,
            'category_id': category_id,
            'partner_id': partner_id,
            'author_id': author_id,
            'created_by_id': created_by_id
        }
        new_ticket = request.env['request.request'].sudo().create(create_vals)
        resp_vals = {
            'id': new_ticket.id,
            'remote_ticket_link': new_ticket.ticket_link
        }
        content = json.dumps(resp_vals, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)

    @http.route(['/helpdesk/api_move_request'],
                auth="none", type='http', methods=['POST'], csrf=False)
    def api_move_request(self, **kw):
        local_ticket = request.env['request.request'].sudo().search([('id', '=', kw['request_id'])], limit=1)
        if safe_eval(kw['remote_route_id']):
            domain = [('remote_id', '=', safe_eval(kw['remote_route_id']))]
        else:
            domain = [('id', '=', safe_eval(kw['route_id']))]
        local_route = request.env['request.stage.route'].sudo().search(domain, limit=1)
        local_ticket.api_move_request(local_route.id, skip_sync=True)
        resp_vals = {}
        content = json.dumps(resp_vals, sort_keys=True, indent=4, cls=ResponseEncoder)
        return Response(content, content_type='application/json;charset=utf-8', status=200)