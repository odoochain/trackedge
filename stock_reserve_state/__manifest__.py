# -*- coding: utf-8 -*-
# Copyright 2024 Trackedge <https://trackedgetechnologies.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{'name': 'Stock Reservation State',
 'summary': 'Stock reservations on products',
 'version': '14.0.1.0.0',
 'author': "Camptocamp,Odoo Community Association (OCA)",
 'category': 'Warehouse',
 'license': 'AGPL-3',
 'complexity': 'normal',
 'website': "https://github.com/OCA/stock-logistics-warehouse",
 'depends': ['stock', 'product_state', 'stock_reserve'],
 'data': [
    'data/product_state.xml',
    #'views/stock_reserve.xml',
    'views/product.xml',
],
 'auto_install': False,
 'installable': True,
 }
