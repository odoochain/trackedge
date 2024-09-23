# -*- coding: utf-8 -*-
# Copyright 2021 Trackedge <https://trackedgetechnologies.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields, api, _
from odoo.tools.float_utils import float_round
from odoo.tools import float_compare
from odoo.exceptions import UserError

TYPE = [
    ('faulty', 'Faulty'),
    ('onhold', 'On Hold')
]


class StockReservation(models.Model):
    _inherit = 'stock.reservation'

    type = fields.Selection(TYPE, default='onhold')
    tracking = fields.Selection(related='product_id.tracking')


    def update_lot_state(self):
        faulty_state = self.env.ref('stock_reserve_state.product_state_faulty')
        onhold_state = self.env.ref('stock_reserve_state.product_state_onhold')
        for this in self:
            for line in this.move_line_ids:
                if this.type and line.lot_id:
                    if this.type == 'faulty':
                        line.lot_id.state_id = faulty_state.id
                    if this.type == 'onhold':
                        line.lot_id.state_id = onhold_state.id
