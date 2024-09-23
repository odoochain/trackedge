# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'General Requests DSK',
    'summary': """Helpdesk""",
    'version': '17.0.0.0.0',
    'license': 'AGPL-3',
    'category': 'After-Sales',
    'author': 'Trackedge',
    'depends': [
        'base',
        'generic_request',
        'stock',
        # 'web_notify',
        'ims_stock',
        # 'sequence_reset_period',
        'generic_request_dsk_region',
        'ims_base'  # since we need the contact form view.

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
