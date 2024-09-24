# -*- coding: utf-8 -*-

from odoo import models, fields, api
import requests
import json
from odoo.exceptions import ValidationError
from odoo.tools.translate import _
import xmlrpc.client


CONTACTUS = [
    # ("nps", "NPS"),
    # ("nes", "NES"),
    ("its", "IT"),
    # ("hr", "HR"),
    # ("other", "OTHERS")
]

class SystrayIcon(models.TransientModel):
    _name = 'help.icons'
    _description = 'Help Icon'

    name = fields.Char(string='Name', required='True')
    email = fields.Char(string='Email', required='True')
    # description = fields.Text(string='Description', required='True')
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    t_type_nps = fields.Many2one('formio.builder', 'Ticket Type', domain=[('nps', '=', True), ('state', '=', 'CURRENT')])
    t_type_nes = fields.Many2one('formio.builder', 'Ticket Type', domain=[('nes', '=', True), ('state', '=', 'CURRENT')])
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
        # if self.t_type_nps and self.t_type_nps.allow_force_update_stage_group_ids
        m = """
        t_type_nps
        t_type_nes
        t_type_its
        t_type_hr
        t_type_other
        """
        if self.contact_us_about == 'nps':
            if not self.t_type_nps:
                raise ValidationError(_("Please select the ticket type"))
            else:
                if not self.t_type_nps.pub_url:
                    url = self.t_type_nps.public_url + '?instance=%s' % instance + '?uemail=%s' % self.email + '?ucompany=%s' % self.env.user.company_id.name
                    return {'type': 'ir.actions.act_url',
                            'url': url,
                            'target': 'new',
                            }
                else:
                    url = self.t_type_nps.pub_url + '?instance=%s' % instance + '?uemail=%s' % self.email + '?ucompany=%s' % self.env.user.company_id.name
                    print(self.t_type_nps.pub_url)
                    return { 'type': 'ir.actions.act_url',
                     'url': url,
                     'target': 'new',
                         }
        elif self.contact_us_about == 'nes':

            if not self.t_type_nes:
                raise ValidationError(_("Please select the ticket type"))

            if not self.t_type_nes:
                raise ValidationError(_("Please select the ticket type"))
            else:
                if not self.t_type_nes.pub_url:
                    url = self.t_type_nes.public_url + '?instance=%s' % instance + '?uemail=%s' % self.email + '?ucompany=%s' % self.env.user.company_id.name
                    return {'type': 'ir.actions.act_url',
                            'url': url,
                            'target': 'new',
                            }
                else:
                    url = self.t_type_nes.pub_url + '?instance=%s' % instance + '?uemail=%s' % self.email + '?ucompany=%s' % self.env.user.company_id.name
                    return {'type': 'ir.actions.act_url',
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
                'url': 'https://trackedgetechnologies.com/helpdesk',
                'target': 'new',
                }


class CustomPopMessage(models.TransientModel):
    _name = "custom.pop.message"

    name = fields.Char('Message')
