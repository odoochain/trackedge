# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'General Requests DSK',
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
        'helpdesk_dsk_region',
        'trackedge_base'  # since we need the contact form view.

    ],
    'data': [
        'security/ir.model.access.csv',
        'data/routine_request_category.xml',
        'views/res_config_settings.xml',
        'views/request_request.xml',
        'views/res_partner_companies.xml',
        'views/res_partner_view.xml',
        'views/stock_picking.xml',
        'views/res_company.xml',
    ],
    'application': False,
    'installable': True,
}
