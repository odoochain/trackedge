# -*- coding: utf-8 -*-
# Copyright 2021 Trackedge <https://trackedgetechnologies.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields

STATE = [
    ('ACTIVE', 'ACTIVE'),
    ('VALIDATED', 'VALIDATED'),
    ('PENDING', 'PENDING')
]


class ItemFrequency(models.Model):
    _name = 'item.frequency'
    _description = 'Product Frequency'
    _sql_constraints = [
        ('name_uniq', 'UNIQUE (name)',
         'Frequency Name must be Unique!')
    ]

    name = fields.Char('Frequency', required=True)
    state = fields.Selection(string="Status", selection=STATE, default='ACTIVE')
    description = fields.Text('Description')
    report_label = fields.Char('Report Label')
