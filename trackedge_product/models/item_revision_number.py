# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ItemRevisionNumber(models.Model):
    _name = 'item.revision.number'
    _description = 'Revision Number'
    _sql_constraints = [
        ('name_uniq', 'UNIQUE (name)',
         'Revision number be Unique!')
    ]
    name = fields.Char('Revision Number', required=True)
    description = fields.Text('Description')

    @api.model
    def create(self, vals):
        # if 'name' in vals:
        if self.search([('name', '=', vals)], limit=1):
            raise ValidationError('Revision Number must be unique.')
        ret = super(ItemRevisionNumber, self).create(vals)
        return ret
