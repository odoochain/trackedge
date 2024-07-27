# Copyright 2024 Trackedge <https://trackedgetechnologies.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    company_code = fields.Char('Company Code', required=True)