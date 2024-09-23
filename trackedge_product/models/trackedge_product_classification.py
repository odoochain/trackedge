# -*- coding: utf-8 -*-
# Copyright 2021 Trackedge <https://trackedgetechnologies.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp


class trackedgeProductClass(models.Model):
    _name = 'trackedge.product.class'
    _description = 'Product Class'
    _order = 'name ASC'
    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Class Name Must Be unique!"),
    ]

    name = fields.Char(string='Class Name', required=True)


STATE = [('ACTIVE', 'ACTIVE'),
         ('VALIDATED', 'VALIDATED'),
         ('PENDING', 'PENDING'), ]
CRITICALITY = [('Critical', 'Critical'),
               ('Non Critical', 'Non Critical')]


class trackedgeProductCategory(models.Model):
    _name = 'trackedge.product.category'
    _description = 'Product Category'
    _order = 'name ASC'
    _sql_constraints = [
        ('name_class_id_uniq', 'unique (class_id,name)',
         "Category must be unique per Class!"),
    ]

    name = fields.Char(string='Category Name', required=True)
    class_id = fields.Many2one('trackedge.product.class', 'Class',
                               ondelete='restrict',
                               required=True)
    type_ids = fields.Many2many('item.type', 'product_id', 'type_id',
                                ondelete='restrict', string="Types")
    required_fields = fields.Char('Required Fields')
    state = fields.Selection(selection=STATE, string="Status", default='ACTIVE')
    system_category = fields.Many2one('system.category', 'System Category')
    noneditable_fields = fields.Char('Non Editable Fields')
    uom_id = fields.Many2one('uom.uom', 'UoM')
    description = fields.Text('Description')
    dim_height = fields.Float(
        'Dim Height',
        digits='Product Unit of Measure')
    dim_length = fields.Float('Dim Length', digits=
        'Product Unit of Measure')
    dim_width = fields.Float('Dim Width',
        digits='Product Unit of Measure')
    physical_weight = fields.Float(digits='Stock Weight')
    shipping_weight = fields.Float(digits='Stock Weight')
    recycle_value_tier = fields.Float(digits='Product Price')
    repair_effectiveness = fields.Float(digits='Product Price')
    reuse_tier = fields.Float(digits='Product Price')
    standard_delivery_method = fields.Char('')
    standard_delivery_time = fields.Datetime('')
    criticality = fields.Selection(string="Status", selection=CRITICALITY,
        default='Critical')
    item_type_ids = fields.Many2many('item.type')
    require_serial_number = fields.Boolean()
    frequency_ids = fields.Many2many(
        'item.frequency',
        'item_type_category_relation',
        'category_id',
        'frequency_id',
        string='Frequency'
    )


class trackedgeProductType(models.Model):
    _name = 'trackedge.product.type'
    _description = 'Product Type'
    _order = 'name ASC'
    _sql_constraints = [
        ('name_category_id_uniq', 'unique (name,category_id)',
         "Type must be unique per Category!"),
    ]

    name = fields.Char(string='Type Name', required=True)
    category_id = fields.Many2one('trackedge.product.category', 'Category',
                                  ondelete='restrict',
                                  required=True)
