# -*- coding: utf-8 -*-
# Copyright 2024 Trackedge <https://trackedgetechnnologies.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields

STATE = [
    ('ACTIVE', 'ACTIVE'),
    ('VALIDATED', 'VALIDATED'),
    ('PENDING', 'PENDING')
]


class TechnologyType(models.Model):
    _name = 'technology.type'
    _description = 'Product Technology Type'
    _sql_constraints = [
        ('name_uniq', 'UNIQUE (name)', 'Technology Type must be Unique!')
    ]

    name = fields.Char('Technology Type', required=True)
    state = fields.Selection(string="Status", selection=STATE, default='ACTIVE')
    description = fields.Text('Description')
    report_label = fields.Char('Report Label')
    repair_effectiveness = fields.Char('Repair Effectiveness')
