# -*- coding: utf-8 -*-
# GreenSystem.
{
    "name": "Mobile Web Interface for Odoo Community version 14.0",
    "description": "Improve Mobile Web Backend Interface for more user friendly and better experience (UI/UX) with "
                   "smart buttons (fab) and mobile responsive for Odoo Community version 14.0. "
                   "Easier to manage your business by smart phone",
    "summary": "Improve Mobile Web Backend Interface for more user friendly and better experience (UI/UX) with "
               "smart buttons (fab) and mobile responsive for Odoo Community version 14.0. "
               "Easier to manage your business by smart phone",
    "version": "14.0.1.0.2",
    "category": "Extra Tools",
    "author": "GreenSystem",
    "license": "OPL-1",
    "sequence": 1,
    "website": "",
    "depends": ["web"],
    "excludes": [
        "web_enterprise",
    ],
    "data": [
        "data/resources.xml",
        "views/templates.xml"
    ],
    "qweb": ["static/src/xml/templates.xml"],
    "images": [
        'static/description/banner.png',
        'static/description/icon.png'
    ],
    # 'live_test_url': 'http://118.70.239.209:8888/',
    "currency": "USD",
    "price": 17.7,
    "maintainer": ["GreenSystem Co., Ltd"],
    "installable": True,
    "auto_install": False,
}
