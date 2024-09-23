##################################################################################

import operator
from odoo import api, fields, models, tools, _


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    fa_icon = fields.Char()
    css_class = fields.Char()
