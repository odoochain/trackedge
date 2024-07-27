# -*- coding: utf-8 -*-
# Copyright 2024 Trackedge <https://trackedgetechnologies.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api, _

class ResCompany(models.Model):
    _inherit = 'res.company'

    logo_mobile = fields.Binary()
    logo_report = fields.Binary()