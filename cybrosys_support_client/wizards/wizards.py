# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import models, fields, api
import requests
import json
from odoo.exceptions import ValidationError
from odoo.tools.translate import _
import xmlrpc.client


CONTACTUS = [
    ("trackedge", "Trackedge"),
    ("its", "IT"),
]

class SystrayIcon(models.TransientModel):
    _name = 'help.icons'
    _description = 'Help Icon'

    name = fields.Char(string='Name', required='True')
    email = fields.Char(string='Email', required='True')
    # description = fields.Text(string='Description', required='True')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    t_type_trackedge = fields.Many2one('formio.builder', 'Ticket Type', domain=[('trackedge', '=', True), ('state', '=', 'CURRENT')])
    t_type_its = fields.Many2one('formio.builder', 'Ticket Type', domain=[('its', '=', True), ('state', '=', 'CURRENT')])
    t_type_hr = fields.Many2one('formio.builder', 'Ticket Type',
        domain=[('hr', '=', True), ('state', '=', 'CURRENT')])
    t_type_other = fields.Many2one('formio.builder', 'Ticket Type',
        domain=[('other', '=', True), ('state', '=', 'CURRENT')])
    user_id = fields.Many2one('res.users', 'Reported Users')
    contact_us_about = fields.Selection(
        CONTACTUS,
        "Contact us about", default="its"
    )

    @api.model
    def default_get(self, field_list):
        result = super(SystrayIcon, self).default_get(field_list)
        result['name'] = self.env.user.name
        if not self.env.user.email:
            result['email'] = self.env.user.login
        else:
            result['email'] = self.env.user.email

        return result


    def confirm_button(self):
        IrConfig = self.env["ir.config_parameter"].sudo()
        instance = IrConfig.get_param('web.base.url')
        # if self.t_type_trackedge and self.t_type_trackedge.allow_force_update_stage_group_ids
        if self.contact_us_about == 'trackedge':
            if not self.t_type_trackedge:
                raise ValidationError(_("Please select the ticket type"))
            else:
                if not self.t_type_trackedge.pub_url:
                    url = self.t_type_trackedge.public_url + '?instance=%s' % instance + '?uemail=%s' % self.email + '?ucompany=%s' % self.env.user.company_id.name
                    return {'type': 'ir.actions.act_url',
                            'url': url,
                            'target': 'new',
                            }
                else:
                    url = self.t_type_trackedge.pub_url + '?instance=%s' % instance + '?uemail=%s' % self.email + '?ucompany=%s' % self.env.user.company_id.name
                    print(self.t_type_trackedge.pub_url)
                    return { 'type': 'ir.actions.act_url',
                     'url': url,
                     'target': 'new',
                         }
        elif self.contact_us_about == 'its':
            if not self.t_type_its:
                raise ValidationError(_("Please select the ticket type"))
            else:
                if not self.t_type_its.pub_url:
                    url = self.t_type_its.public_url + '?instance=%s' % instance + '?uemail=%s' % self.email + '?ucompany=%s' % self.env.user.company_id.name
                    return {'type': 'ir.actions.act_url',
                            'url': url,
                            'target': 'new',
                            }
                else:
                    url = self.t_type_its.pub_url + '?instance=%s' % instance + '?uemail=%s' % self.email + '?ucompany=%s' % self.env.user.company_id.name
                    return {'type': 'ir.actions.act_url',
                            'url': url,
                            'target': 'new',
                            }
        elif self.contact_us_about == 'hr':
            if not self.t_type_hr:
                raise ValidationError(_("Please select the ticket type"))
            else:
                if not self.t_type_hr.pub_url:
                    url = self.t_type_hr.public_url + '?instance=%s' % instance + '?uemail=%s' % self.email + '?ucompany=%s' % self.env.user.company_id.name
                    return {'type': 'ir.actions.act_url',
                            'url': url,
                            'target': 'new',
                            }
                else:
                    url = self.t_type_hr.pub_url + '?instance=%s' % instance + '?uemail=%s' % self.email + '?ucompany=%s' % self.env.user.company_id.name
                    return {'type': 'ir.actions.act_url',
                            'url': url,
                            'target': 'new',
                            }
        elif self.contact_us_about == 'other':
            if not self.t_type_other:
                raise ValidationError(_("Please select the ticket type"))
            else:
                if not self.t_type_other.pub_url:
                    url = self.t_type_other.public_url + '?instance=%s' % instance + '?uemail=%s' % self.email + '?ucompany=%s' % self.env.user.company_id.name
                    return {'type': 'ir.actions.act_url',
                            'url': url,
                            'target': 'new',
                            }
                else:
                    url = self.t_type_other.pub_url + '?instance=%s' % instance + '?uemail=%s' % self.email + '?ucompany=%s' % self.env.user.company_id.name
                    return {'type': 'ir.actions.act_url',
                            'url': url,
                            'target': 'new',
                            }

    def my_tickets(self):
        return {'type': 'ir.actions.act_url',
                'url': 'https://web.trackedgetech.com/helpdesk',
                'target': 'new',
                }


class CustomPopMessage(models.TransientModel):
    _name = "custom.pop.message"

    name = fields.Char('Message')
