# Copyright 2018 Barroux Abbey (https://www.barroux.org/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, _
from odoo.exceptions import UserError


class FruitJuiceProductionCompensation(models.TransientModel):
    _name = 'fruit.juice.production.product.swap'
    _description = 'Swap juice type on fruit juice production'

    production_id = fields.Many2one(
        'fruit.juice.production', string='Fruit Juice Production', required=True)
    palox_id = fields.Many2one(
        related='production_id.palox_id', readonly=True)
    farmers = fields.Char(
        related='production_id.farmers', readonly=True)
    season_id = fields.Many2one(
        related='production_id.season_id', readonly=True)
    juice_destination = fields.Selection(
        related='production_id.juice_destination', readonly=True)
    current_juice_product_id = fields.Many2one(
        related='production_id.juice_product_id', readonly=True,
        string='Current Juice Type')
    new_juice_product_id = fields.Many2one(
        'product.product', string='New Juice Type',
        domain=[('fruit_type', '=', 'juice')], required=True)
    sale_location_id = fields.Many2one(
        'stock.location', string='New Sale Tank')

    def validate(self):
        self.ensure_one()
        prod = self.production_id
        cur_product = self.current_juice_product_id
        cur_fruit_culture_type = cur_product.fruit_culture_type
        new_product = self.new_juice_product_id
        new_fruit_culture_type = new_product.fruit_culture_type
        if (
                cur_fruit_culture_type in ('regular', 'conversion') and
                new_fruit_culture_type == 'organic'):
            raise UserError(_(
                "You cannot swap juice type from a regular or conversion "
                "culture type to an organic culture type."))
        elif (
                cur_fruit_culture_type in ('regular', 'organic') and
                new_fruit_culture_type == 'conversion'):
            raise UserError(_(
                "You cannot swap juice type from a regular or organic "
                "culture type to a conversion culture type."))
        sloc = prod.warehouse_id.fruit_get_shrinkage_tank(new_product)
        prod_vals = {
            'juice_product_id': new_product.id,
            'sale_location_id': self.sale_location_id.id or False,
            'shrinkage_location_id': sloc.id,
            }
        prod.write(prod_vals)
        prod.line_ids.write({'juice_product_id': new_product.id})
        prod.message_post(_(
            "Juice Type changed from %s to %s via the swap juice type wizard.")
            % (cur_product.name, new_product.name))
        return True
