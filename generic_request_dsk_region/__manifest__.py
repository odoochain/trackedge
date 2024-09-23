# Copyright 2021 Trackedge
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Generic Request Region',
    'summary': """ Helpdesk Ticket Region """,
    'version': '17.0.0.0.0',
    'license': 'AGPL-3',
    'category': 'After-Sales',
    'author': 'Trackedge',
    'depends': [
        'generic_request',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/helpdesk_region.xml',
    ],
    'application': False,
    'installable': True,
}
