# -*- coding: utf-8 -*-
# Copyright 2024 Trackedge <https://trackedgetechnnologies.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields

STATE = [
    ('ACTIVE', 'ACTIVE'),
    ('VALIDATED', 'VALIDATED'),
    ('PENDING', 'PENDING')
]


class ItemOem(models.Model):
    _name = 'item.oem'
    _description = 'Item OEM'

    name = fields.Char('OEM Name', required=True)
    state = fields.Selection(string="Status", selection=STATE, default='ACTIVE')
    description = fields.Text('Description')
    report_label = fields.Char('Report Label')
    _sql_constraints = [
        ('name_uniq', 'UNIQUE (name)',
         'Item Type must be Unique!')
    ]
