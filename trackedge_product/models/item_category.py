# -*- coding: utf-8 -*-
# Copyright 2024 Trackedge <https://trackedgetechnnologies.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons import decimal_precision as dp
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

STATE = [
    ('ACTIVE', 'ACTIVE'),
    ('VALIDATED', 'VALIDATED'),
    ('PENDING', 'PENDING')
]

CRITICALITY = [
    ('Critical', 'Critical'),
    ('Non Critical', 'Non Critical')
]


class ItemCategory(models.Model):
    _name = 'item.category'
    _description = 'Item Category'

    name = fields.Char('Category Name', required=True)
    required_fields = fields.Char('Required Fields')
    state = fields.Selection(string="Status",
                             selection=STATE, default='ACTIVE')
    system_category = fields.Many2one('system.category', 'Sytem Category')
    noneditable_fields = fields.Char('Non Editable Fields')
    uom_id = fields.Many2one('uom.uom', 'UoM')
    description = fields.Text('Description')
    dim_height = fields.Float(
        'Dim Height',
        digits='Product Unit of Measure')
    dim_length = fields.Float('Dim Length',
        digits='Product Unit of Measure')
    dim_width = fields.Float('Dim Width',
        digits='Product Unit of Measure')
    physical_weight = fields.Float(digits='Stock Weight')
    shipping_weight = fields.Float(digits='Stock Weight')
    recycle_value_tier = fields.Float(digits='Product Price')
    repair_effectiveness = fields.Float(digits='Product Price')
    reuse_tier = fields.Float(digits='Product Price')
    standard_delivery_method = fields.Char('')
    standard_delivery_time = fields.Datetime('')
    criticality = fields.Selection(
        selection=CRITICALITY, default='Critical')
    item_type_ids = fields.Many2many('item.type')
    require_serial_number = fields.Boolean()
    frequency_ids = fields.Many2many('item.frequency')
    report_label = fields.Char()

    @api.model
    def create(self, vals):
        if 'name' in vals:
            if self.search([('name', '=', vals['name'])], limit=1):
                raise UserError('Item Category Name must be unique.')
        ret = super(ItemCategory, self).create(vals)
        return ret
