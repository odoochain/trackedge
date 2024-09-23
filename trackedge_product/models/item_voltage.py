# -*- coding: utf-8 -*-
# Copyright 2021 Trackedge <https://trackedgetechnologies.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields

STATE = [
    ('ACTIVE', 'ACTIVE'),
    ('VALIDATED', 'VALIDATED'),
    ('PENDING', 'PENDING')
]


class ItemVoltage(models.Model):
    _name = 'item.voltage'
    _description = 'Item Voltage'
    _sql_constraints = [('name_unique', 'UNIQUE (name)',
                         'Voltage Name must be Unique!')]

    name = fields.Char('Voltage', required=True)
    description = fields.Text('Description')
    state = fields.Selection(string="Status", selection=STATE, default='ACTIVE')
