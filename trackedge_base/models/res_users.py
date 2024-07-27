# -*- coding: utf-8 -*-
# Copyright 2024 Trackedge <https://trackedgetechnologies.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields, api, _

NOTIFICATION_TYPE = [
    ('sms', 'SMS Notifications'),
    ('whatsapp', 'Whatsapp Notifications')
]


class ResUsers(models.Model):
    _inherit = 'res.users'

    is_engineer = fields.Boolean()
    sms_notification = fields.Boolean()
    wa_notification = fields.Boolean()
    notification_type = fields.Selection([
        ('email', 'Handle by Emails'),
        ('inbox', 'Handle in Trackedge')],
        'Notification', required=True, default='email',
        help="Policy on how to handle Chatter notifications:\n"
             "- Handle by Emails: notifications are sent to your email address\n"
             "- Handle in Trackedge: notifications appear in your Trackedge Inbox")
    odoobot_state = fields.Selection(
        [
            ('not_initialized', 'Not initialized'),
            ('onboarding_emoji', 'Onboarding emoji'),
            ('onboarding_attachement', 'Onboarding attachement'),
            ('onboarding_command', 'Onboarding command'),
            ('onboarding_ping', 'Onboarding ping'),
            ('idle', 'Idle'),
            ('disabled', 'Disabled'),
        ], string="Bot Status", readonly=True,
        required=False)  # keep track of the state: correspond to the code of the last message sent

    # TODO: these onchange are not working
    @api.onchange('sms_notification')
    def _onchange_sms_notification(self):
        partner_id = self.partner_id
        if partner_id:
            partner_id.sms_notification = self.sms_notification

    @api.onchange('wa_notification')
    def _onchange_wa_notification(self):
        for this in self:
            for partner in this.partner_id:
                partner.wa_notification = this.wa_notification


    def unlink(self):
        # Delete related partner when user is deleted
        related_partners = self.mapped('partner_id')
        ret = super(ResUsers, self).unlink()
        related_partners.unlink()
        return ret

    def write(self, vals):
        # Deactivate related partner when user is deactivated
        ret = super(ResUsers, self).write(vals)
        if 'active' in vals:
            self.mapped('partner_id').write({'active': vals['active']})
        if 'wa_notification' in vals:
            self.mapped('partner_id').write({'wa_notification': vals['wa_notification']})
        return ret
