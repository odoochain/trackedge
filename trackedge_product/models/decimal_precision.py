# -*- coding: utf-8 -*-
# Copyright 2024 Trackedge <https://trackedgetechnnologies.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields, api, _


class DecimalPrecision(models.Model):
    _inherit = 'decimal.precision'

    @api.model
    def set_all_precision_to_zero(self):
        decimal_precision = self.search([])
        for this in decimal_precision:
            this.digits = 0
