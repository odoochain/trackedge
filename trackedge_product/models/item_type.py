# -*- coding: utf-8 -*-
# Copyright 2024 Trackedge <https://trackedgetechnnologies.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields

STATE = [
    ('ACTIVE', 'ACTIVE'),
    ('VALIDATED', 'VALIDATED'),
    ('PENDING', 'PENDING')
]


class ItemType(models.Model):
    _name = 'item.type'
    _description = 'Item Type'

    name = fields.Char('Item Type', required=True)
    description = fields.Text('Description')
    state = fields.Selection(string="Status", selection=STATE, default='ACTIVE')
    _sql_constraints = [
        ('name_uniq', 'UNIQUE (name)',
         'Item Type must be Unique!')
    ]
