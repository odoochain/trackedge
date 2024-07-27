# -*- coding: utf-8 -*-

from odoo import api, fields, models

# -*- coding: utf-8 -*-

import time
from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import get_lang



class ReportJournal(models.AbstractModel):
    _name = 'report.generic_request.report_request_type'
    _description = 'Request by Request Type Report'

    def lines(self, request_type, data):
        if data['form'].get('date_from'):
            date_from = data['form'].get('date_from')
        if data['form'].get('date_to'):
            date_to = data['form'].get('date_to')
        res_line = []
        res_line_dict = {}
        max_time = 0
        min_time = 0
        avg_time = 0
        open_tickets = self.env['request.request'].search_count([
                ('date_created', '>=', date_from),
                ('date_created', '<=', date_to),
                ('closed', '=', False),
                ('type_id', '=', request_type)
            ])
        print ('ggg', open_tickets)
        close_tickets = self.env['request.request'].search_count([
                ('date_created', '>=', date_from),
                ('date_created', '<=', date_to),
                ('closed', '=', True),
                ('type_id', '=', request_type)
            ])
        
        print ('ggg111', close_tickets)
        # return self.env['request.request'].search([('type_id', '=', request_type), ('')])
        res_line_dict['open_tickets'] = open_tickets
        res_line_dict['close_tickets'] = close_tickets
        res_line_dict['max_time'] = max_time
        res_line_dict['min_time'] = min_time
        res_line_dict['avg_time'] = avg_time
        res_line.append(res_line_dict)
        return res_line


    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))


        res = {}
        for request_type in data['form']['request_type_ids']:
            res[request_type] = self.with_context(data['form'].get('used_context', {})).lines(request_type, data)
        print ('GGGGGGGGGGG')
        print (res)
        return {
            'doc_ids': data['form']['request_type_ids'],
            'doc_model': self.env['request.type'],
            'data': data,
            'lines': res,
            'docs': self.env['request.type'].browse(data['form']['request_type_ids']),
            'time': time,
        }





class RequestTypeCommonReport(models.TransientModel):
    _name = "request.type.common.report"
    _description = "Request Type Common Report"

    request_type_ids = fields.Many2many('request.type', string='Request Types', required=True, default=lambda self: self.env['request.type'].search([]))
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')


    def _build_contexts(self, data):
        result = {}
        result['request_type_ids'] = 'request_type_ids' in data['form'] and data['form']['request_type_ids'] or False
        result['date_from'] = data['form']['date_from'] or False
        result['date_to'] = data['form']['date_to'] or False
        return result

    def _print_report(self, data):
        return self.env.ref('generic_request.action_report_request_type').report_action(self, data=data)

    def check_report(self):
        self.ensure_one()
        data = {}
        data['ids'] = self.env.context.get('active_ids', [])
        data['model'] = self.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(['date_from', 'date_to', 'request_type_ids'])[0]
        used_context = self._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=get_lang(self.env).code)
        return self.with_context(discard_logo_check=True)._print_report(data)