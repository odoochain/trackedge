from odoo import models, fields, api
from odoo.osv import expression

STATUS = [
    ('nff', 'No Fault Found'),
    ('faulty', 'Faulty'),
    ('rok', 'ROK'),
    ('ber', 'BER'),
]


class RepairFaultCode(models.Model):
    _name = "stock.repair.code"
    _description = "Repair codes for Stocks"

    _sql_constraints = [
        ('name_uniq', 'unique (name)',
         'Name should be unique!'),
    ]

    name = fields.Char(string='Repair Code', required=True, help="G123")
    description = fields.Char(string='Repair Description')
    action_taken = fields.Char(string='Action Taken')
    status = fields.Selection(string='Status', selection=STATUS)

    @api.model
    def create(self, vals):
        if 'name' in vals:
            existing = self.search([('name', '=', vals['name'])], limit=1)
            if existing:
                vals['name'] = vals['name'] + '_NEW'
        return super(RepairFaultCode, self).create(vals)
    @api.model
    def _name_search1(self, name='', args=None, operator='ilike', limit=100,
                     name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', '|', ('name', '=ilike', name), ('name', operator, name), '|', ('description', '=ilike', name),
                      ('description', operator, name)]
            if operator in expression.NEGATIVE_TERM_OPERATORS:
                domain = ['&', '!'] + domain[1:]
        repair_code_ids = self._search(expression.AND([domain, args]),
                              limit=limit, access_rights_uid=name_get_uid)
        return repair_code_ids #self.browse(repair_code_ids).name_get()

    def name_get(self):
        res = []
        for repair_code in self:
            name = '[%s] %s' % (repair_code.name, repair_code.description)
            res.append((repair_code.id, name))
        return res
