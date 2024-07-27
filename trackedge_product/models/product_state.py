# -*- coding: utf-8 -*-
# Copyright 2024 Trackedge <https://trackedgetechnnologies.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields, api, _


class ProductState(models.Model):
    _inherit = 'product.state'

    color = fields.Char(string="Color", help="Choose state color")
