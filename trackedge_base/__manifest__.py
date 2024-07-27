# -*- coding: utf-8 -*-
# Copyright 2024 Trackedge <https://trackedgetechnologies.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Trackedge Base',
    'version': '14.0.1.0.0',
    'category': 'Stock',
    'sequence': 1,
    'summary': 'Trackedge Bundle',
    'author': 'Trackedge',
    "website": "https://trackedgetechnologies.com",
    "license": "AGPL-3",
    'depends': [
        'base',
        'stock',
        'contacts',
        'uom',
    ],
    'data': [
        'security/trackedge_security.xml',
        'security/ir.model.access.csv',
        'data/res_lang.xml',
        'views/res_company.xml',
        'views/menu.xml',
        'views/res_users.xml',
        'views/res_config_settings_routines.xml'
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
