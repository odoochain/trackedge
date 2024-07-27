# Copyright 2024 Trackedge <https://trackedgetechnologies.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from re import findall

from datetime import date, datetime
from odoo import models, fields, api, _, SUPERUSER_ID, tools
from odoo.exceptions import Warning, ValidationError, UserError


class RequestRequestRoute(models.Model):
    _name = 'request.request.route'
    _description = 'HD Routes'
    _rec_name = 'location_id'
    """Routes Through which an item will be delivered"""

    servicedesk_id = fields.Many2one('request.request')
    sequence = fields.Integer()
    warehouse_id = fields.Many2one('stock.warehouse')
    warehouse_loc_id = fields.Many2one('stock.location',
        related='warehouse_id.view_location_id')
    warehouse_dest_id = fields.Many2one('stock.warehouse')
    warehouse_dest_loc_id = fields.Many2one('stock.location',
        related='warehouse_dest_id.view_location_id')
    location_id = fields.Many2one('stock.location', 'From')
    location_dest_id = fields.Many2one('stock.location', 'To')
    picking_id = fields.Many2one('stock.picking')

    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):
        if self.warehouse_id:
            self.location_id = self.warehouse_id.lot_stock_id.id

    @api.onchange('warehouse_dest_id')
    def _onchange_warehouse_dest_id(self):
        if self.warehouse_dest_id:
            self.location_dest_id = self.warehouse_dest_id.lot_stock_id.id


class RequestRequest(models.Model):
    _inherit = 'request.request'
    """All links between helpdesk and stock picking"""

    location_id = fields.Many2one('stock.location', string="Location")
    picking_ids = fields.One2many(
        'stock.picking',
        'servicedesk_id',
        string='Stock Move',
        domain=[('state', '!=', 'cancel')]
    )
    route_ids = fields.One2many(
        'request.request.route',
        'servicedesk_id',
        string='Picking Routes'
    )

    shipping_order = fields.Many2one('stock.picking')
    receiving_order = fields.Many2one('stock.picking')
    transfer_order = fields.Many2one('stock.picking')

    # create picking, create move ids
    def _create_picking(self):
        self.ensure_one()
        picking = False
        picking_vals = self.env.context.get('picking_vals', False)
        if picking_vals:
            picking = self.env['stock.picking'].create({
                'picking_type_id':picking_vals['picking_type_id'],
                'location_id': picking_vals['location_id'],
                'location_dest_id': picking_vals['location_dest_id'],
                'servicedesk_id': picking_vals['servicedesk_id'],
                'pick_type': picking_vals['pick_type'],
                'company_id': picking_vals['company_id'],
                'site_id': picking_vals['site_id'],
                'criticality': picking_vals['criticality'],
                'hd_ticket': picking_vals['hd_ticket'],
                'nmc_ticket': picking_vals['nmc_ticket'],
                'order_type_id': picking_vals['order_type_id'],
                'mr_date': picking_vals['mr_date'],
                'owner_id': picking_vals['owner_id'],
                'location_dest_func_id': picking_vals['location_dest_func_id']
            })
        return picking


    def group_lines(self, lines):
        lines_grouped = {}
        for line in self.stock_move_location_line_ids:
            lines_grouped.setdefault(
                line.product_id.id,
                self.env["wiz.stock.move.location.line"].browse(),
            )
            lines_grouped[line.product_id.id] |= line
        return lines_grouped

    def _get_move_values(self, picking, line):
        # locations are same for the products
        product = line['product_id']
        return {
            "name": product.display_name,
            "location_id": picking.location_id.id,
            "location_dest_id": picking.location_dest_id.id,
            "product_id": product.id,
            "product_uom": product.uom_id.id,
            "product_uom_qty": line['qty'],
            "picking_id": picking.id,
            "location_move": True,
        }


    def _create_move(self, picking, line):
        self.ensure_one()
        move = self.env["stock.move"].create(
            self._get_move_values(picking, line),
        )
        return move


    def _create_moves(self, picking):
        self.ensure_one()
        lines = self.env.context.get('picking_lines')
        moves = self.env["stock.move"]
        for line in lines:
            move = self._create_move(picking, line)
            moves |= move
        return moves


    def _create_hd_picking(self):
        picking = self._create_picking()
        self._create_moves(picking)
        return picking


