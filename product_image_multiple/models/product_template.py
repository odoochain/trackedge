# -*- coding: utf-8 -*-
# Copyright 2024 Trackedge <https://trackedgetechnologies.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models, fields, api

LAYOUTS = [
    ('1x', '1x'),
    ('2x', '2x'),
    ('3x', '3x'),
]


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    image_layout = fields.Selection(LAYOUTS, string='Image Layout',
                                    default='2x')
    video_youtube_layout = fields.Selection(LAYOUTS,
                                            string='Youtube Video Layout',
                                            default='2x')
    kanban_display_popup = fields.Boolean(string='Popup Display', default=False)
    image_ids = fields.One2many('product.template.image', 'product_id')
    youtube_video_ids = fields.One2many('product.template.youtube.video',
                                        'product_id')

    def open_multi_image_view(self):
        self.ensure_one()

        view_id = self.env.ref(
            'product_image_multiple.view_form_wizard_product_template_multi_images')
        return {'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'product.template',
                'target': self.kanban_display_popup and 'new',
                'res_id': self.id,
                'view_id': view_id.id,
                }

    def open_video_view(self):
        self.ensure_one()
        view_id = self.env.ref(
            'product_image_multiple.view_form_wizard_product_template_videos')

        return {'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'view_type': 'form',
                'res_model': 'product.template',
                'target': self.kanban_display_popup and 'new',
                'res_id': self.id,
                'view_id': view_id.id,
                }


class ProductTemplateImage(models.Model):
    _name = 'product.template.image'
    _description = 'Product Image'

    product_id = fields.Many2one('product.template', ondelete='cascade')
    image_layout_style = fields.Char(compute='_compute_image_layout_style')
    image = fields.Binary(string='Image', required=True)

    def _compute_image_layout_style(self):
        for rec in self:
            rec.image_layout_style = \
            {'1x': 'width:100%', '2x': 'width:42%', '3x': 'width:29%'}[
                rec.product_id.image_layout]


class ProductTemplateYoutubeVideo(models.Model):
    _name = 'product.template.youtube.video'
    _description = 'Youtube Video'

    product_id = fields.Many2one('product.template', ondelete='cascade')
    link = fields.Char(required=True)
    video_code = fields.Char(compute='_compute_video_code')
    youtube_layout_style = fields.Char(compute='_compute_video_layout_style')

    def _compute_video_layout_style(self):
        for rec in self:
            rec.youtube_layout_style = \
            {'1x': 'width:100%', '2x': 'width:42%', '3x': 'width:29%'}[
                rec.product_id.video_youtube_layout]

    def _compute_video_code(self):
        for record in self:
            try:
                code = record.link.split('youtu.be/')[1]
                record.video_code = code

            except Exception as e:
                record.video_code = 'none'
