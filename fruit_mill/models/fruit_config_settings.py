# Copyright 2018 Barroux Abbey (https://www.barroux.org/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import models, fields


class FruitConfigSettings(models.TransientModel):
    _name = 'fruit.config.settings'
    _inherit = 'res.config.settings'

    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.user.company_id, required=True)
    current_season_id = fields.Many2one(
        related='company_id.current_season_id', readonly=True)
    fruit_harvest_arrival_max_delta_days = fields.Integer(
        related='company_id.fruit_harvest_arrival_max_delta_days')
    fruit_max_qty_per_palox = fields.Integer(
        related='company_id.fruit_max_qty_per_palox')
    fruit_appointment_qty_per_palox = fields.Integer(
        related='company_id.fruit_appointment_qty_per_palox')
    fruit_appointment_arrival_no_leaf_removal_minutes = fields.Integer(
        related='company_id.fruit_appointment_arrival_no_leaf_removal_minutes')
    fruit_appointment_arrival_leaf_removal_minutes = fields.Integer(
        related='company_id.fruit_appointment_arrival_leaf_removal_minutes')
    fruit_appointment_arrival_min_minutes = fields.Integer(
        related='company_id.fruit_appointment_arrival_min_minutes')
    fruit_appointment_lend_minutes = fields.Integer(
        related='company_id.fruit_appointment_lend_minutes')
    fruit_appointment_withdrawal_minutes = fields.Integer(
        related='company_id.fruit_appointment_withdrawal_minutes')
    fruit_shrinkage_ratio = fields.Float(
        related='company_id.fruit_shrinkage_ratio')
    fruit_filter_ratio = fields.Float(
        related='company_id.fruit_filter_ratio')
    fruit_min_ratio = fields.Float(
        related='company_id.fruit_min_ratio')
    fruit_max_ratio = fields.Float(
        related='company_id.fruit_max_ratio')
    fruit_juice_density = fields.Float(
        related='company_id.fruit_juice_density')
    fruit_juice_leaf_removal_product_id = fields.Many2one(
        related='company_id.fruit_juice_leaf_removal_product_id')
    fruit_juice_production_product_id = fields.Many2one(
        related='company_id.fruit_juice_production_product_id')
    fruit_juice_tax_product_id = fields.Many2one(
        related='company_id.fruit_juice_tax_product_id')
    fruit_juice_early_bird_discount_product_id = fields.Many2one(
        related='company_id.fruit_juice_early_bird_discount_product_id')
    fruit_juice_production_start_hour = fields.Integer(
        related='company_id.fruit_juice_production_start_hour')
    fruit_juice_production_start_minute = fields.Integer(
        related='company_id.fruit_juice_production_start_minute')
    fruit_juice_analysis_default_user_id = fields.Many2one(
        related='company_id.fruit_juice_analysis_default_user_id')
    fruit_juice_production_duration_minutes = fields.Integer(
        related='company_id.fruit_juice_production_duration_minutes')
