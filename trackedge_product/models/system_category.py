# -*- coding: utf-8 -*-
# Copyright 2021 Trackedge <https://trackedgetechnologies.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields

STATE = [
    ('ACTIVE', 'ACTIVE'),
    ('VALIDATED', 'VALIDATED'),
    ('PENDING', 'PENDING'),
    ('IMPORTED', 'IMPORTED')
]


class SystemCategory(models.Model):
    _name = 'system.category'
    _description = 'System category'
    _sql_constraints = [
        ('name_uniq', 'UNIQUE (name)',
         'System Category must be Unique!')
    ]

    name = fields.Char('System Category', required=True)
    state = fields.Selection(string="Status", selection=STATE, default='ACTIVE')
    description = fields.Text('Description')
    report_label = fields.Char('Report Label')
    repair_effectiveness = fields.Char('Repair Effectiveness')
