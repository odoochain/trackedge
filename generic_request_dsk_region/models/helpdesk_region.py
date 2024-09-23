# Copyright 2021 Trackedge
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from odoo.exceptions import UserError


class HelpdeskRegion(models.Model):
    _name = "helpdesk.region"
    _description = "helpdesk.region"
    _rec_name = 'name'

    supervisor_id = fields.Many2one(
        'res.partner',
        'Supervisor ID',
        required=True
    )
    name = fields.Char('Name', required=True)
    description = fields.Text('Description')

    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Name Must be Unique!')
    ]

    @api.model
    def create(self, values):
        # This is to help in importation
        # if add debugger to see values being exported
        # not csv and excel have different approaches.
        if 'supervisor_id' not in values:
            msg = "%s requires a supervisor."
            self.env.user.notify_danger(message='Supervisor is required')
        if 'supervisor_id' in values and values['supervisor_id'] is False:
            msg = "%s requires a supervisor."
            self.env.user.notify_danger(message='Supervisor cannot be False, '
                                                'add a supervisor')
        return super(HelpdeskRegion, self).create(values)

