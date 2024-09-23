from odoo import models, fields, api
from odoo.osv import expression


class Delivery(models.Model):
    _name = "delivery.condition"
    _description = "Physical condition of delivery"

    _sql_constraints = [
        ('name_uniq', 'unique (name)',
         'Name should be unique!'),
    ]

    name = fields.Char(string='Delivery Condition Code', required=True, help="A")
    description = fields.Char(string='Delivery Condition Description')
    appearance_performance = fields.Char(string='Delivery Appearance / Performance')
    
    @api.model
    def create(self, vals):
        if 'name' in vals:
            existing = self.search([('name', '=', vals['name'])], limit=1)
            if existing: 
                vals['name'] = vals['name'] + '_NEW'
        return super(Delivery, self).create(vals)
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
        condition_ids = self._search(expression.AND([domain, args]),
                              limit=limit, access_rights_uid=name_get_uid)
        return condition_ids #self.browse(condition_ids).name_get()

    def name_get(self):
        res = []
        for condition in self:
            name = '(%s) %s' % (condition.name, condition.description)
            res.append((condition.id, name))
        return res
