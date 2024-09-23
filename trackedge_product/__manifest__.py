# -*- coding: utf-8 -*-
# Copyright 2021 Trackedge <https://trackedgetechnologies.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Trackedge Product',
    'version': '17.0.0.0.0',
    'category': 'Stock',
    'sequence': 1,
    'summary': 'Trackedge trackedge Bundle',
    'author': 'Trackedge',
    "website": "https://trackedgetechnologies.com",
    "license": "OPL-1",
    'images': ['images/main_screenshot.png'],
    'summary': 'This module is used for NIM-NES Connection',
    'depends': [
        'base',
        'stock',
        'trackedge_base'
        # 'uom',
        # 'stock_change_qty_reason',
        # 'product_state',
        # 'product_pack',
        # 'trackedge_base',
        # 'stock_available',
        # 'stock_available_immediately',
        # 'stock_available_unreserved',
        # 'product_image_multiple',
        # 'stock_reserve_state',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/trackedge_product_class.xml',
        'data/delivery_condition.xml',
        'data/stock_condition.xml',
        'data/stock_fault_code.xml',
        'data/stock_repair_code.xml',
        'views/item_oem.xml',
        'views/uom_uom.xml',
        'views/uom_category.xml',
        'views/product_classification.xml',
        'views/item_type.xml',
        'views/system_category.xml',
        'views/system_type.xml',
        'views/technology_type.xml',
        'views/item_voltage.xml',
        'views/item_frequency.xml',
        # 'views/item_category.xml',
        'views/product_template.xml',
        'views/product_product.xml',
        'wizards/stock_warehouse_orderpoint_wizard.xml',
        'views/product_state.xml',
        'views/stock_fault_code.xml',
        'views/stock_repair_code.xml',
        'views/stock_condition.xml',
        'views/delivery_condition.xml',
        'views/product_template_product_state_views.xml',
        'views/product_state_views.xml'
    ],
    'demo': [],
    'test': [],
    'css': [],
    'js': [],
    'price': 0.0,
    'currency': 'EUR',
    'installable': True,
    'application': False,
    'auto_install': False,
}