# -*- coding: utf-8 -*-
# Copyright 2024 Trackedge <https://trackedgetechnnologies.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields, api, _, exceptions


class UnitOfMeasure(models.Model):
    _inherit = 'uom.uom'

    _sql_constraints = [
        ('name_uniq', 'unique(name)',
         "Unit of measure must be unique!"),
    ]

    @api.constrains('name')
    def uom_name_size(self):
        if self.name and len(self.name) > 50:
            raise exceptions.Warning("Name cannot exceed 50 characters!")


class UnitCategory(models.Model):
    _inherit = 'uom.category'

    _sql_constraints = [
        ('name_uniq', 'unique(name)',
         "Unit of measure Category must be unique!"),
    ]

    @api.constrains('name')
    def uom_category(self):
        if self.name and len(self.name) > 50:
            raise exceptions.Warning("Name cannot exceed 256 characters!")
