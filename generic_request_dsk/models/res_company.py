# Copyright 2021 Trackedge
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    company_code = fields.Char('Company Code', required=True)