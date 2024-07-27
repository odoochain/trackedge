# -*- coding: utf-8 -*-
# Copyright 2024 Trackedge <https://trackedgetechnologies.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    onhold_count = fields.Float(
        compute='_compute_reservation_count',
        string='# On Hold', digits='Stock Threshold')

    faulty_count = fields.Float(
        compute='_compute_reservation_count',
        string='# Faulty', digits='Stock Threshold')


    def _compute_reservation_count(self):
        ret = super(ProductTemplate, self)._compute_reservation_count()
        for product in self:
            product.onhold_count = sum(
                product.product_variant_ids.mapped('onhold_count'))
            product.faulty_count = sum(
                product.product_variant_ids.mapped('faulty_count'))
        return ret


    def action_view_reservations(self):
        self.ensure_one()
        type = self.env.context.get('type', False)
        ref = 'stock_reserve.action_stock_reservation_tree'
        product_ids = self.mapped('product_variant_ids.id')
        action_dict = self.env.ref(ref).read()[0]
        action_dict['domain'] = [('product_id', 'in', product_ids)]
        action_dict['context'] = {
            'search_default_draft': 1,
            'search_default_reserved': 1,
            'default_product_id': product_ids[0],
            'default_type': type
        }
        return action_dict


class ProductProduct(models.Model):
    _inherit = 'product.product'

    onhold_count = fields.Float(
        compute='_compute_reservation_count',
        string='# On Hold', digits='Stock Threshold')

    faulty_count = fields.Float(
        compute='_compute_reservation_count',
        string='# Faulty', digits='Stock Threshold')


    def _compute_reservation_count(self):
        ret = super(ProductProduct, self)._compute_reservation_count()
        for product in self:
            domain = [('product_id', '=', product.id),
                      ('state', 'not in', ['cancel'])]
            reservations = self.env['stock.reservation'].search(domain)
            onhold = reservations.filtered(lambda x: x.type == 'onhold')
            faulty = reservations.filtered(lambda x: x.type == 'faulty')
            product.onhold_count = sum(onhold.mapped('product_qty'))
            product.faulty_count = sum(faulty.mapped('product_qty'))
        return ret

    def action_view_reservations(self):
        self.ensure_one()
        ref = 'stock_reserve.action_stock_reservation_tree'
        action_dict = self.env.ref(ref).read()[0]
        action_dict['domain'] = [('product_id', '=', self.id)]
        action_dict['context'] = {
            'search_default_draft': 1,
            'search_default_reserved': 1
        }
        return action_dict
