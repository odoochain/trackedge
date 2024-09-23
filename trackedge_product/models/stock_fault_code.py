from odoo import models, fields, api
from odoo.osv import expression

STATUS = [
    ('nff', 'NFF'),
    ('faulty', 'Faulty'),
    ('rok', 'ROK'),
    ('ber', 'BER'),
    ('onhold', 'On Hold'),
]


class StockFaultCode(models.Model):
    _name = "stock.fault.code"
    _description = "Fault codes for Stocks"

    _sql_constraints = [
        ('name_uniq', 'unique (name)',
         'Name should be unique!'),
    ]

    name = fields.Char(string='Fault Code', required=True, help="F123")
    description = fields.Char(string='Fault Description')
    status = fields.Selection(string='Status', selection=STATUS)
    shortlisted = fields.Boolean(string="Is Shortlisted")

    @api.model
    def create(self, vals):
        if 'name' in vals:
            existing = self.search([('name', '=', vals['name'])], limit=1)
            if existing:
                vals['name'] = vals['name'] + '_NEW'
        return super(StockFaultCode, self).create(vals)

    @api.model
    def _name_search1(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None, order=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', '|', ('name', '=ilike', name), ('name', operator, name), '|', ('description', '=ilike', name),
                      ('description', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        fault_code_ids = self._search(expression.AND([domain, args]),
                              limit=limit, access_rights_uid=name_get_uid)
        return fault_code_ids #self.browse(fault_code_ids).name_get()

    def name_get(self):
        res = []
        for fault_code in self:
            name = '[%s] %s' % (fault_code.name, fault_code.description)
            res.append((fault_code.id, name))
        return res
