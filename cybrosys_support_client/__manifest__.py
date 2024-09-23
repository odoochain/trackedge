# -*- coding: utf-8 -*-

{
    'name': "Odoo Support Request",
    'category': 'Productivity',
    'summary': 'Create Odoo Support Request To Cybrosys',
    'version': '17.0.1.0.1',
    'description': """Odoo Support""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'maintainer': 'Cybrosys Techno Solutions',
    'license': 'LGPL-3',
    'depends': ['base','formio', 'base_setup'],
    'assets': {
        'web.assets_backend': [
            'cybrosys_support_client/static/src/js/systray_theme_menu.js',
            'cybrosys_support_client/static/src/xml/systray_icon.xml',
        ]
    },
    'data': [
        'security/ir.model.access.csv',
        'wizards/wizards.xml',
        'views/fomio_builder.xml'
    ],
    'images': [
        'static/description/banner.png',
    ],

}
