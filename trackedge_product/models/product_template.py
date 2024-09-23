# -*- coding: utf-8 -*-
# Copyright 2021 Trackedge <https://trackedgetechnologies.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import base64

import requests
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons import decimal_precision as dp
from boto3.session import Session
from .product_product import ITEM_TYPE
from odoo.addons.stock.models.product import OPERATORS

ITEM_STATUS = [
    ('ACTIVE', 'ACTIVE'),
    ('VALIDATED', 'VALIDATED'),
    ('SUSPECT', 'SUSPECT'),
    ('IMPORTED', 'IMPORTED')
]

POWER_TYPE = [
    ('AC', 'AC'),
    ('DC', 'DC'),
    ('AC/DC', 'AC/DC'),
    ('None', 'None'),
    ('PASSIVE', 'PASSIVE')
]

SOFTWARE_DEPENDANCY = [
    ('FULLYDEPENDENT', 'FULLYDEPENDENT'),
    ('PARTIALLYDEPENDENT', 'PARTIALLYDEPENDENT'),
    ('NOTDEPENDENT', 'NOTDEPENDENT')
]
spare_criticality = [
    ('critical_spare', 'Critical Spare'),
    ('non_critical_spares', 'Non Critical Spare')
]
itemkit = [
    ('oem', 'OEM'),
    ('custom', 'Custom')
]

fields_to_hide_in_search = ['description_purchase', 'description_sale', 'sequence', 'description_purchase',
                            'description_sale', 'rental', 'color', 'image_layout', 'video_youtube_layout',
                            'kanban_display_popup', 'pack_type', 'pack_component_price', 'pack_ok', 'pack_modifiable',
                            'description_picking', 'description_pickingout', 'purchase_method', 'purchase_line_warn',
                            'service_type', 'sale_line_warn', 'sale_line_warn_msg', 'expense_policy', 'invoice_policy',
                            'can_be_used_for_coverage_report_ept', 'service_to_purchase', 'stock_state_threshold',
                            'manual_stock_state_threshold', 'hs_code', 'comment', 'comment2', 'speed', 'owner_id',
                            'barcode_img', 'barcode2_img', 'default_reuse_group', 'has_custom_fields', 'user_id',
                            'life_time', 'use_time', 'removal_time', 'alert_time', 'spares_criticality', 'remote_id',
                            'part_image_url', 'should_override_default_oem_replace_price', 'part_image_name',
                            'purchase_ok', 'sale_ok', 'create_uid', 'create_date', 'write_uid', 'write_date',
                            'message_main_attachment_id', 'model', 'voltage', 'state', 'responsible_id']


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    _order = 'name ASC'

    default_code = fields.Char(string='Item #', copy=True, index=True)
    name = fields.Char(string='Item Description')
    alternative_name = fields.Char('Alt Part#')
    pack_ok = fields.Boolean(string="Is Kit")
    comment = fields.Text(string="Comment")
    comment2 = fields.Text(string="Alt Comment")
    speed = fields.Char(string='Speed')
    voltage = fields.Char(string='Potential Difference')  # Voltage
    service_status_id = fields.Many2one('product.state',
                                        string='Service status')
    # manufacturer = fields.Char(string='Manufacturer', size=50)
    model = fields.Char(string='Model')
    warranty = fields.Integer(string='Warranty')
    warranty_uom_id = fields.Many2one('uom.uom', string='Warranty Dimension')
    weight = fields.Float(string='Unit Weight',
        digits='Product Unit of Measure')
    weight_uom_id = fields.Many2one('uom.uom', string='Weight Dimension')
    standard_price = fields.Float(string='Unit Cost',
        digits='Product Price')
    list_price = fields.Float(string='Unit Price',
        digits='Product Price')
    owner_id = fields.Many2one('res.partner', string="Customer", domain=[
        ('is_owner', '=', True)])
    class_id = fields.Many2one(
        'trackedge.product.class',
        string="Item Class"
    )
    category_id = fields.Many2one('item.category')
    type_ids = fields.Many2many('item.type', string="Item Type IDs")
    revision_number = fields.Char('Rev#')
    revision_number_ids = fields.Many2many('item.revision.number', string='Rev#')
    aka = fields.Char(string='AKA')
    aka2 = fields.Char('AKA 2')
    oem_id = fields.Many2one('item.oem', 'OEM')
    erp_code = fields.Char('ERP Code')
    erp_code2 = fields.Char('ERP Code2')
    oem_alt_part_number = fields.Many2one('product.product', 'OEM Alt Part#')
    clei_num = fields.Char('CLEI')
    warranty_until_date = fields.Date(string='Warranty Until date')
    system_category_id = fields.Many2one('system.category', 'System Category')
    system_type_ids = fields.Many2many('system.type', string='System Type')
    technology_type_ids = fields.Many2many(
        'technology.type',
        'item_technology_type_rel',
        'item_id',
        'type_id',
        string='Technology Type')
    frequency_ids = fields.Many2many('item.frequency', string='Frequency')
    power_type = fields.Selection(string='Power Type',
                                  selection=POWER_TYPE)
    voltage_id = fields.Many2one('item.voltage', 'Voltage')
    amp_hours = fields.Float()
    max_watt = fields.Float()
    min_watt = fields.Float()
    lifespan_in_months = fields.Integer()
    software_dependency = fields.Selection(
        selection=SOFTWARE_DEPENDANCY)
    software_info = fields.Char('Software')
    max_operating_temp = fields.Float('Max. Temp')
    min_operating_temp = fields.Float('Min. Temp')
    is_snmp_enabled = fields.Boolean('SNMP Enabled')
    first_sold_date = fields.Date('First Sold Date')
    last_sold_date = fields.Date('Last Sold Date')
    end_of_life = fields.Boolean('End of Life?')
    end_of_life_date = fields.Date('')
    end_of_service = fields.Date('')
    physical_height = fields.Float()
    physical_length = fields.Float()
    physical_weight = fields.Float()
    physical_width = fields.Float()
    shipping_height = fields.Float()
    shipping_length = fields.Float()
    shipping_weight = fields.Float()
    shipping_width = fields.Float()
    spec_sheet_doc = fields.Binary('Spec Sheet')
    warranty_doc = fields.Binary('Warranty Document')
    barcode2 = fields.Char('Barcode2')
    market_availability_tier = fields.Float('Market Availability Tier',
        digits='Product Price')
    market_avail_qty = fields.Float('Market Availability Qty',
        digits='Stock Threshold')
    high_runner_code = fields.Float('High Runner Code',
        digits='Stock Threshold')
    fault_rate = fields.Float('Fault Rate')
    recycle_value_tier = fields.Float('Recycle Value Tier',
        digits='Product Price')
    repair_effectiveness = fields.Float('Repair Effectiveness',
        digits='Product Price')
    recycled_value_class = fields.Char('Recycled Value Class')
    recycle_gwp_ratio = fields.Float('Recycle GWP Ratio', digits='Product Price')
    reuse_event_gwp_ratio = fields.Float('Reuse event GWP Ratio', digits='Product Price')
    extended_life_gwp_ratio = fields.Float('Extended Life GWP Ratio', digits='Product Price')
    repair_price = fields.Float('Repair Price', digits='Product Price')
    aftermarket_buy_price = fields.Float('Aftermarket Buy Price', digits='Product Price')
    aftermarket_replace_price = fields.Float('Aftermarket Replace Cost', digits='Product Price')

    spares_criticality = fields.Selection(spare_criticality)
    warranty_until_date = fields.Date()
    oem_replace_price = fields.Float('OEM Replace Price')
    barcode_img = fields.Binary('Barcode1 Image')
    barcode2_img = fields.Binary('Barcode2 Image')
    notes = fields.Text('Notes')
    value_per_kg = fields.Float(digits='Product Unit of Measure')
    default_reuse_group = fields.Char('')
    l1_refurb = fields.Char('')
    l2_refurb = fields.Char('')
    l3_refurb = fields.Char('')
    item_type = fields.Selection(ITEM_TYPE, default='ACTIVE')
    item_status = fields.Selection(ITEM_STATUS, default='ACTIVE')
    has_custom_fields = fields.Boolean()
    user_id = fields.Many2one('res.users', default=lambda s: s.env.uid)
    remote_id = fields.Integer(default=0)
    part_image_name = fields.Char()
    part_image_url = fields.Binary(
        string='Part Image URL',
        compute="get_image_url",
        attachment=True,
        store=True,
        tracking=False
    )
    # image = fields.Binary(string="Item Image", attachment=True, help="")
    # image_medium = fields.Binary("Medium-sized image", attachment=True, help="")
    # image_small = fields.Binary("Small-sized image", attachment=True, help="")
    item_class_type = fields.Char('Item Class Type')
    kit_type = fields.Selection(itemkit, 'Kit Type')
    # kit_items_ids = fields.Many2many('product.product', string='Kit Items')
    should_override_default_oem_replace_price = fields.Boolean(default=False)
    source_last_updated_time = fields.Datetime()

    # is_nim_item = fields.Boolean(compute='compute_nim_item')
    #
    # @api.mutli
    # def compute_nim_item(self):
    #     class_id = self.env.ref("trackedge_product.item_class_consumable")
    #     for this in self:
    #         if this.class_id == class_id:
    #             this.is_nim_item = False
    #         else:
    #             this.is_nim_item = True

    def action_product_replenish(self):
        action = self.env.ref('stock.action_product_replenish').read()[0]
        return action

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        default = dict(default or {})
        if default.get(self.default_code, False):
            return super().copy(default)
        default.setdefault('default_code', '')
        return super().copy(default)

    @api.constrains('default_code')
    def check_default_code(self):
        # self.ensure_one()
        for this in self:
            if this.default_code:
                domain = [
                    '&',
                    ('id', '!=', this.id),
                    ('default_code', '=', this.default_code)
                ]
                products = self.env['product.template'].search(domain)
                if products:
                    raise UserError(
                        "Item# %s already exists" % this.default_code)

    @api.constrains('erp_code')
    def check_erp_code(self):
        self.ensure_one()
        if self.erp_code:
            domain = [
                '&',
                ('id', '!=', self.id),
                ('erp_code', '=', self.erp_code)
            ]
            code = self.env['product.template'].search(domain)
            if code:
                raise UserError(
                    "ERP Code %s already exists@" % self.erp_code)

    @api.onchange('pack_line_ids')
    def _onchange_pack_line_ids(self):
        for this in self:
            if not this.pack_line_ids:
                this.pack_ok = False
            else:
                this.pack_ok = True

    def validate_item_change_rights(self):
        if self.env.context.get('force_item_create', False):
            return
        if not self.env.user.has_group('trackedge_base.group_create_product'):
            raise UserError('You are not allowed to create/edit any item in trackedge')

    def validate_item_change_class(self, vals):
        consu = self.env.ref("trackedge_product.item_class_consumable").id
        if 'class_id' in vals and vals['class_id'] != consu:
            raise UserError('Your only allowed to create consumable products.')

    @api.model
    def create(self, vals):
        # User can only create consumables the rest he/she needs access rights
        self.validate_item_change_rights()
        # self.validate_item_change_class(vals)
        return super(ProductTemplate, self).create(vals)

    def write(self, vals):
        self.validate_item_change_rights()
        # self.validate_item_change_class(vals)
        return super(ProductTemplate, self).write(vals)

    def unlink(self):
        # consu = self.env.ref("trackedge_product.item_class_consumable").id
        for record in self:
            vals = {'class_id': record.class_id.id}
            self.validate_item_change_rights()
            # self.validate_item_change_class(vals)
        return super(ProductTemplate, self).unlink()

    def get_image_url(self):
        IrDefault = self.env['ir.default'].sudo()
        for this in self:
            this.part_image_url = ''
        try:
            upload_bucket = IrDefault.get(
                'res.config.settings', "aws_upload_bucket")
            aws_access_key_id = IrDefault.get(
                'res.config.settings', "aws_access_key_id")
            aws_secret_access_key = IrDefault.get(
                'res.config.settings', "aws_secret_access_key")
            region_name = IrDefault.get(
                'res.config.settings', "aws_region_name")
            session = Session(aws_access_key_id=aws_access_key_id,
                              aws_secret_access_key=aws_secret_access_key, region_name=region_name)
            s3Client = session.client('s3')
        except Exception as e:
            print("Error occurred in getting aws settings.")
            for record in self:
                record.part_image_url = ''
            return
        for record in self:
            if record.part_image_name:
                key = record.part_image_name
                image = None
                try:
                    part_image_url = s3Client.generate_presigned_url('get_object',
                                                                     Params={'Bucket': upload_bucket, 'Key': key},
                                                                     ExpiresIn=100)
                except Exception as e:
                    print("Error occurred in generating image url for %s." % record.default_code)
                    return
                print("AWS image url for %s part: %s" % (record.default_code, part_image_url))
                if part_image_url:
                    image = base64.b64encode(requests.get(part_image_url.strip()).content).replace(b'\n', b'')
                # record.update({'part_image_url': image})
                record.part_image_url = image
            else:
                record.part_image_url = ''
                print("Image doesn't exists for part %s." % record.default_code)

    def fields_get1(self, fields=None):
        res = super(ProductTemplate, self).fields_get()
        for field in fields_to_hide_in_search:
            if res.get(field):
                res.get(field)['searchable'] = False
                res.get(field)['sortable'] = False
        return res

    # stock_available code
    @api.depends(
        "product_variant_ids.immediately_usable_qty",
        "product_variant_ids.potential_qty",
    )
    def _compute_available_quantities(self):
        res = self._compute_available_quantities_dict()
        for product in self:
            for key, value in res[product.id].items():
                if key in product._fields:
                    product[key] = value

    def _compute_available_quantities_dict(self):
        variants_dict, _ = self.mapped(
            "product_variant_ids"
        )._compute_available_quantities_dict()
        res = {}
        for template in self:
            immediately_usable_qty = sum(
                [
                    variants_dict[p.id]["immediately_usable_qty"]
                    - variants_dict[p.id]["potential_qty"]
                    for p in template.product_variant_ids
                ]
            )
            potential_qty = max(
                [
                    variants_dict[p.id]["potential_qty"]
                    for p in template.product_variant_ids
                ]
                or [0.0]
            )
            res[template.id] = {
                "immediately_usable_qty": immediately_usable_qty + potential_qty,
                "potential_qty": potential_qty,
            }
        return res

    immediately_usable_qty = fields.Float(
        digits="Product Unit of Measure",
        compute="_compute_available_quantities",
        search="_search_immediately_usable_qty",
        string="Available to promise",
        help="Stock for this Product that can be safely proposed "
             "for sale to Customers.\n"
             "The definition of this value can be configured to suit "
             "your needs",
    )
    potential_qty = fields.Float(
        compute="_compute_available_quantities",
        digits="Product Unit of Measure",
        string="Potential",
        help="Quantity of this Product that could be produced using "
             "the materials already at hand. "
             "If the product has several variants, this will be the biggest "
             "quantity that can be made for a any single variant.",
    )

    @api.model
    def _search_immediately_usable_qty(self, operator, value):
        """Search function for the immediately_usable_qty field.
        The search is quite similar to the Odoo search about quantity available
        (addons/stock/models/product.py,253; _search_product_quantity function)
        :param operator: str
        :param value: str
        :return: list of tuple (domain)
        """
        products = self.search([])
        # Force prefetch
        products.mapped("immediately_usable_qty")
        product_ids = []
        for product in products:
            if OPERATORS[operator](product.immediately_usable_qty, value):
                product_ids.append(product.id)
        return [("id", "in", product_ids)]

    # stock_available_unreserved
    qty_available_not_res = fields.Float(
        string="Quantity On Hand Unreserved",
        digits="Product Unit of Measure",
        compute="_compute_product_available_not_res",
        search="_search_quantity_unreserved",
        help="Quantity of this product that is "
             "not currently reserved for a stock move",
    )

    @api.depends("product_variant_ids.qty_available_not_res")
    def _compute_product_available_not_res(self):
        for tmpl in self:
            if isinstance(tmpl.id, models.NewId):
                continue
            tmpl.qty_available_not_res = sum(
                tmpl.mapped("product_variant_ids.qty_available_not_res")
            )

    def action_open_quants_unreserved(self):
        products_ids = self.mapped("product_variant_ids").ids
        quants = self.env["stock.quant"].search([("product_id", "in", products_ids)])
        quant_ids = quants.filtered(
            lambda x: x.product_id.qty_available_not_res > 0
        ).ids
        result = self.env.ref("stock.group_stock_multi_locations").read()[0]
        result["domain"] = [("id", "in", quant_ids)]
        result["context"] = {
            "search_default_locationgroup": 1,
            "search_default_internal_loc": 1,
        }
        return result

    def _search_quantity_unreserved(self, operator, value):
        return [("product_variant_ids.qty_available_not_res", operator, value)]
