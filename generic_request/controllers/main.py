# -*- coding: utf-8 -*-


from odoo import http
from odoo.http import request


class HelpdeskWeb(http.Controller):

    # @http.route(['/helpdesk'], type="http", auth="user", website=True)
    # def tickets(self):
    #     tickets = request.env['request.request'].search([])
    #     values = {
    #         'tickets': tickets,
    #     }
    #     return request.render("generic_request.ticket", values)

    # @http.route(['/tickets/details/<model("request.request"):ticket>'], type="http", auth="user", website=True)
    # def tickets_details(self, ticket):
    #     values = {
    #         'tickets': ticket,
    #     }
    #     return {'type': 'ir.actions.act_url',
    #                 'url': 'https://trackedgetechnologies.com/web#action=459&model=request.request&view_type=kanban&cids=&menu_id=335',
    #                 'target': 'self',
    #                 }
    
    @http.route(["/requests/pass"],
                type='http', auth="public", website=True)
    def request_pass(self, **kw):
        request_id = int(kw.get('id'))
        req_id = request.env['request.request'].sudo().browse(request_id)
        stage_type_id = request.env['request.stage.type'].sudo().search([('code', '=', 'close')], limit=1)
        if stage_type_id:
            req_id.sudo().write({'stage_type_id': stage_type_id.id})
        return http.request.redirect("/helpdesk/request/%s" %(request_id))
        # return http.request.render("generic_request.mail_requests_pass")


    @http.route(["/requests/failed"],
                type='http', auth="public",
                website=True)
    def request_failed(self, **kw):
        request_id = int(kw.get('id'))
        req_id = request.env['request.request'].sudo().browse(request_id)

        stage_type_id = request.env['request.stage.type'].sudo().search([('code', '=', 'uat-failed')], limit=1)
        if stage_type_id:
            req_id.sudo().write({'stage_type_id': stage_type_id.id})
        if req_id.stage_id.code == 'uat-failed':
            stage_type_qc_id = request.env['request.stage.type'].sudo().search([('code', '=', 'qc')], limit=1)
            if stage_type_qc_id:
                req_id.sudo().write({'stage_type_id': stage_type_qc_id.id})
        return http.request.redirect("/helpdesk/request/%s" %(request_id))
        # return http.request.render("generic_request.mail_requests_failed")

