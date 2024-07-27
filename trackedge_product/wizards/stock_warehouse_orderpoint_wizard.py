# -*- coding: utf-8 -*-
# Copyright 2024 Trackedge <https://trackedgetechnnologies.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields, api, _
from odoo.addons import decimal_precision as dp

class ProductTemplate(models.Model):
    _inherit = 'product.template'


    def update_reorder_levels(self):
        self.ensure_one()
        warehouses = self.env['stock.warehouse'].search([])
        wiz = self.env['stock.warehouse.orderpoint.wizard'].create(
            {'name': 'Reorder Levels for [%s]' % self.product_variant_id.name,
             'product_id': self.product_variant_id.id}
        )
        existing_orderpoints = self.env['stock.warehouse.orderpoint'].search(
            [('product_id', '=', self.product_variant_id.id)])

        for warehouse in warehouses:
            exisiting_orderpoint_line = existing_orderpoints.filtered(
                lambda x: x.warehouse_id.id == warehouse.id)
            for orderpoint in exisiting_orderpoint_line:
                vals = dict(
                    orderpoint_id=wiz.id,
                    warehouse_id=warehouse.id,
                    location_id=orderpoint.location_id.id,
                    product_min_qty=orderpoint.product_min_qty,
                    product_max_qty=orderpoint.product_max_qty,
                    qty_multiple=orderpoint.qty_multiple
                )
                self.env['stock.warehouse.orderpoint.wizard.line'].create(vals)
            if not exisiting_orderpoint_line:
                vals2 = dict(
                    orderpoint_id=wiz.id,
                    warehouse_id=warehouse.id,
                    location_id=warehouse.lot_stock_id.id
                )
                self.env['stock.warehouse.orderpoint.wizard.line'].create(vals2)

        # location_id = fields.Many2one('stock.location')
        # product_min_qty = fields.Float()
        # product_max_qty = fields.Float()
        # qty_multiple = fields.Float()

        return {
            'name': _('Reorder Levels'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.warehouse.orderpoint.wizard',
            'res_id': wiz.id,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new'
        }


class StockWarehouseOrderpointWizard(models.TransientModel):
    _name = 'stock.warehouse.orderpoint.wizard'
    _description = 'Orderpoints Wizard'

    name = fields.Char()
    product_id = fields.Many2one('product.product')
    orderpoint_ids = fields.One2many(
        'stock.warehouse.orderpoint.wizard.line', 'orderpoint_id')


    def create_orderpoints(self):
        self.ensure_one()
        existing_orderpoints = self.env['stock.warehouse.orderpoint'].search(
            [('product_id', '=', self.product_id.id)])
        for line in self.orderpoint_ids:
            exisiting_orderpoint_line = existing_orderpoints.filtered(
                lambda x: x.warehouse_id.id == line.warehouse_id.id and
                          x.location_id.id == line.location_id.id)
            vals = dict(
                product_min_qty=line.product_min_qty,
                product_max_qty=line.product_max_qty,
                qty_multiple=line.qty_multiple
            )
            if exisiting_orderpoint_line:
                exisiting_orderpoint_line.write(vals)
            else:
                vals['warehouse_id'] = line.warehouse_id.id
                vals['product_id'] = self.product_id.id,
                vals['location_id'] = line.location_id.id,
                self.env['stock.warehouse.orderpoint'].create(vals)


class StockWarehouseOrderpointWizardLine(models.TransientModel):
    _name = 'stock.warehouse.orderpoint.wizard.line'
    _description = 'Orderpoint lines'

    orderpoint_id = fields.Many2one('stock.warehouse.orderpoint.wizard')
    warehouse_id = fields.Many2one('stock.warehouse')
    location_id = fields.Many2one('stock.location')
    product_min_qty = fields.Float(digits='Stock Threshold')
    product_max_qty = fields.Float(digits='Stock Threshold')
    qty_multiple = fields.Float(digits='Stock Threshold')
