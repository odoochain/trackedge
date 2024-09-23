# -*- coding: utf-8 -*-
# Copyright 2021 Trackedge <https://trackedgetechnologies.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields, api
from odoo.exceptions import ValidationError

STATE = [
    ('ACTIVE', 'ACTIVE'),
    ('VALIDATED', 'VALIDATED'),
    ('PENDING', 'PENDING')
]


class SystemType(models.Model):
    _name = 'system.type'
    _description = 'System Type'
    _sql_constraints = [
        ('name_uniq', 'UNIQUE (name, oem_id)', 'System Type + OEM must be Unique!')
    ]

    name = fields.Char('System Type', required=True)
    description = fields.Text('Description')
    oem_id = fields.Many2one('item.oem', 'OEM')
    state = fields.Selection(string="Status", selection=STATE, default='ACTIVE')
    report_label = fields.Char('Report Label')

    @api.constrains('name', 'oem_id')
    def _check_name_oem(self):
        for rec in self:
            if rec.name:
                domain = [('id', '!=', rec.id),('name', '=', rec.name)]
                if rec.oem_id:
                    domain += [('name', '=', rec.oem_id.id)]
                exisiting_rec = self.search(domain)
                if exisiting_rec:
                    raise ValidationError('System Type + OEM must be Unique!')
