# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import json
from json2html import *
from datetime import date, datetime
from odoo import models, fields, api, _, SUPERUSER_ID, tools


class FormioForm(models.Model):
    _inherit = 'formio.form'

    submission_instance = fields.Char()
    submission_email = fields.Char()
    submission_company = fields.Char()
    request_request_id = fields.Many2one('request.request')
    request_type_id = fields.Many2one('request.type', required=True,
        related='builder_id.request_type_id')
    request_category_id = fields.Many2one('request.category',
        related='builder_id.request_category_id')
    default_user_id = fields.Many2one('res.users',
        related='builder_id.default_user_id')

    @api.model
    def create(self, vals):
        urgency = vals.get('urgency', False)
        impact = vals.get('impact', False)
        if urgency:
            if urgency.lower() == 'low':
                urgency = '1'
            if urgency.lower() == 'medium':
                urgency = '2'
            if urgency.lower() == 'high':
                urgency = '3'
            vals.pop('urgency')
        if impact:
            if impact.lower() == 'low':
                impact = '1'
            if impact.lower() == 'medium':
                impact = '2'
            if impact.lower() == 'high':
                impact = '3'
            vals.pop('impact')
        ret = super(FormioForm, self).create(vals)
        schema_data = json.loads(ret.builder_id.schema)
        
        if ret.state == 'COMPLETE':
            submission_data = ret.submission_data
            submission_dict = json.loads(ret.submission_data)
            submission_dict.pop('submit')
            default_user_id = False
            name = ''
            submission_dict_new = {}
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
            author_id = False
            if ret.default_user_id:
                default_user_id = ret.default_user_id.id
            if ret.submission_user_id:
                author_id = ret.submission_user_id.partner_id.id
            else:
                author_id = ret.submission_partner_id and ret.submission_partner_id.id
            attachment_remove = []
            for submit_key, submit_value in submission_dict.items():
                if type(submit_value) == list:
                    for value_list in submit_value:
                        if value_list.get('storage') and value_list.get('storage') == 'url' and value_list.get('url'):
                            attachment_remove.append(submit_key)
            for remove in attachment_remove:
                if remove in submission_dict:
                    submission_dict.pop(remove)
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
            stage_id = ret.request_type_id.start_stage_id.id
            stage_type_id = ret.request_type_id.start_stage_id and ret.request_type_id.start_stage_id.type_id.id
            body = {
                'created_by_id': ret.submission_user_id.id,
                'summary': name,
                'ticket_type': ret.builder_id.id,
                'form_id': ret.id,
                'type_id': ret.request_type_id.id,
                'category_id': ret.request_category_id.id,
                'request_text': submission_table,
                'user_id': default_user_id,
                'author_id': author_id,
                'stage_id': ret.request_type_id.start_stage_id.id,
                'stage_type_id': stage_type_id,
                'urgency': urgency,
                'impact': impact,
            }
            ticket = self.env['request.request'].create(body)
            if ticket.user_id and not ticket.type_id.is_market_place:
                stage_type_id = self.env['request.stage.type'].search([('code', '=', 'assigned')], limit=1)
                if stage_type_id:
                    ticket.write({'stage_type_id': stage_type_id.id})
            # ticket.assign_to_hdo()
            ret.request_request_id = ticket.id
        return ret


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    def write(self, vals):
        ret = super(IrAttachment, self).write(vals)
        if 'res_model' in vals and vals['res_model'] == 'formio.form':
            form = self.env['formio.form'].search([
                ('id', '=', vals['res_id'])], limit=1)
            if form.request_request_id:
                ticket_attachment = {
                    'name': self.name,
                    'res_name': self.res_name,
                    'res_model': 'request.request',
                    'res_id': form.request_request_id.id,
                    'company_id': self.env.company.id,
                    'datas': self.datas
                }
                self.create(ticket_attachment)
        return ret


class FormioBuilder(models.Model):
    _inherit = 'formio.builder'

    request_type_id = fields.Many2one('request.type', required=True)
    request_category_id = fields.Many2one('request.category')
    default_user_id = fields.Many2one('res.users')