# Copyright 2018 Barroux Abbey (https://www.barroux.org/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.tools import float_round
from odoo.exceptions import UserError


class FruitJuiceProductionRatio2force(models.TransientModel):
    _name = 'fruit.juice.production.ratio2force'
    _description = 'Fruit Juice Production Ratio2force'

    production_id = fields.Many2one(
        'fruit.juice.production', string='Fruit Juice Production', required=True)
    farmers = fields.Char(
        related='production_id.farmers', readonly=True)
    palox_id = fields.Many2one(
        related='production_id.palox_id', readonly=True)
    season_id = fields.Many2one(
        related='production_id.season_id', readonly=True)
    juice_product_id = fields.Many2one(
        related='production_id.juice_product_id', readonly=True)
    juice_destination = fields.Selection(
        related='production_id.juice_destination', readonly=True)
    fruit_qty = fields.Float(
        related='production_id.fruit_qty', readonly=True)
    compensation_type = fields.Selection(
        related='production_id.compensation_type', readonly=True)
    compensation_juice_product_id = fields.Many2one(
        related='production_id.compensation_juice_product_id', readonly=True)
    compensation_last_fruit_qty = fields.Float(
        related='production_id.compensation_last_fruit_qty', readonly=True)
    compensation_juice_qty = fields.Float(
        related='production_id.compensation_juice_qty', readonly=True)
    juice_qty_kg = fields.Float(
        string='Juice Qty (kg)', digits=dp.get_precision('Fruit Weight'),
        required=True)
    juice_qty = fields.Float(
        string='Juice Qty (L)', compute='_compute_all',
        digits=dp.get_precision('Fruit Juice Volume'), readonly=True)
    ratio = fields.Float(
        string='Gross Ratio (% L)', compute='_compute_all',
        digits=dp.get_precision('Fruit Juice Ratio'), readonly=True)
    sale_location_id = fields.Many2one(
        'stock.location', string='Sale Tank')
    compensation_sale_location_id = fields.Many2one(
        'stock.location', string='Compensation Sale Tank')
    decanter_duration = fields.Integer(string='Decanter Duration')
    decanter_speed = fields.Integer(
        string='Decanter Speed', compute='_compute_decanter_speed',
        readonly=True)

    @api.depends('juice_qty_kg')
    def _compute_all(self):
        pr_juice = self.env['decimal.precision'].precision_get(
            'Fruit Juice Volume')
        pr_ratio = self.env['decimal.precision'].precision_get(
            'Fruit Juice Ratio')
        for wiz in self:
            density = wiz.production_id.company_id.fruit_juice_density
            juice_qty = 0.0
            ratio = 0.0
            if density:
                juice_qty = wiz.juice_qty_kg / density
                juice_qty = float_round(juice_qty, precision_digits=pr_juice)
            # Compute ratio, with compensations
            juice_qty_for_ratio = juice_qty
            if wiz.compensation_type == 'last':
                juice_qty_for_ratio -= wiz.compensation_juice_qty
            elif wiz.compensation_type == 'first':
                juice_qty_for_ratio += wiz.compensation_juice_qty
            if wiz.fruit_qty:
                ratio = 100 * juice_qty_for_ratio / wiz.fruit_qty
                ratio = float_round(ratio, precision_digits=pr_ratio)
            wiz.ratio = ratio
            wiz.juice_qty = juice_qty

    @api.depends('decanter_duration')
    def _compute_decanter_speed(self):
        for wiz in self:
            decanter_speed = 0
            if wiz.decanter_duration:
                decanter_speed = wiz.fruit_qty * 60 / wiz.decanter_duration
            wiz.decanter_speed = decanter_speed

    def validate(self):
        self.ensure_one()
        prod = self.production_id
        min_ratio, max_ratio = prod.company_id.fruit_min_max_ratio()
        if self.ratio > max_ratio or self.ratio < min_ratio:
            raise UserError(_(
                "The ratio (%s %%) of production %s is not realistic.")
                % (self.ratio, prod.name))
        vals = {
            'juice_qty_kg': self.juice_qty_kg,
            'juice_qty': self.juice_qty,
            'ratio': self.ratio,
            'decanter_speed': self.decanter_speed,
            'compensation_sale_location_id': self.compensation_sale_location_id.id or False,
            'sale_location_id': self.sale_location_id.id or False,
            }
        prod.write(vals)
        prod.ratio2force()
        return True
