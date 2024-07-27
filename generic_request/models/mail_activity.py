# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from datetime import date, datetime
from odoo import models, fields, api, _, SUPERUSER_ID, tools


class ActivityDate(models.Model):
    _inherit = 'mail.activity'

    date_deadline = fields.Date('Due Date', required=True, default=fields.Date.context_today)
    date_deadline_new = fields.Date('Due Date New', default=fields.Date.context_today)
    @api.onchange('date_deadline')
    def previous_date(self):
        for rec in self:
            if rec.date_deadline < fields.Date.today():
                rec.date_deadline = rec.date_deadline_new
