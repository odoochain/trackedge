# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'General Requests - Servicedesk',
    'summary': """Helpdesk""",
    'version': '14.0.1.22.1',
    'license': 'AGPL-3',
    'category': 'After-Sales',
    'author': 'Trackedge',
    'depends': [
        'base',
        'generic_request',
        'stock',
        'web_notify',
        'trackedge_stock',
        'sequence_reset_period',
        'trackedge_base'  # since we need the contact form view.

    ],
    'data': [
        'views/request_request.xml'

    ],
    'application': False,
    'installable': True,
}
