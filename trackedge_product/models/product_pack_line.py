# -*- coding: utf-8 -*-
# Copyright 2021 Trackedge <https://trackedgetechnologies.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductPackLine(models.Model):
    _inherit = 'product.pack.line'

    lot_id = fields.Many2one('stock.production.lot')

    @api.onchange('quantity')
    def onchange_quantity(self):
        if self.quantity and self.quantity <= 0:
            raise ValidationError("Quantity of Kit Component Cannot be 0 or less")

    @api.constrains('quantity')
    def _check_quantity(self):
        for this in self:
            if this.quantity <= 0:
                raise ValidationError("Quantity of Kit Component Cannot be 0 or less")