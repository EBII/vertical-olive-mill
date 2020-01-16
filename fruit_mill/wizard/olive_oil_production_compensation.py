# Copyright 2018 Barroux Abbey (https://www.barroux.org/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.tools import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class FruitJuiceProductionCompensation(models.TransientModel):
    _name = 'fruit.juice.production.compensation'
    _description = 'Enter compensation on fruit juice production'

    production_id = fields.Many2one(
        'fruit.juice.production', string='Fruit Juice Production', required=True)
    warehouse_id = fields.Many2one(
        related='production_id.warehouse_id', readonly=True)
    season_id = fields.Many2one(
        related='production_id.season_id', readonly=True)
    palox_id = fields.Many2one(
        related='production_id.palox_id', readonly=True)
    farmers = fields.Char(
        related='production_id.farmers', readonly=True)
    compensation_type = fields.Selection([
        ('none', 'No Compensation'),
        ('first', 'First of the Day'),
        ('last', 'Last of the Day'),
        ], string='Compensation Type', required=True)
    compensation_location_id = fields.Many2one(
        'stock.location', string='Compensation Tank')
    compensation_last_fruit_qty = fields.Float(
        string='Fruit Compensation Qty',
        digits=dp.get_precision('Fruit Weight'))
    compensation_ratio = fields.Float(
        string='Compensation Ratio',
        digits=dp.get_precision('Fruit Juice Ratio'))
    compensation_ratio_update_date = fields.Date(
        related='production_id.warehouse_id.fruit_juice_compensation_ratio_update_date',
        readonly=True)
    compensation_last_juice_qty = fields.Float(
        compute='_compute_compensation_last_juice_qty',
        string='Juice Compensation (L)', readonly=True,
        digits=dp.get_precision('Fruit Juice Volume'))

    @api.model
    def default_get(self, fields_list):
        res = super(FruitJuiceProductionCompensation, self).default_get(
            fields_list)
        prod = self.env['fruit.juice.production'].browse(
            res.get('production_id'))
        res.update({
            'compensation_type': prod.compensation_type,
            'compensation_location_id': prod.compensation_location_id.id or False,
            'compensation_last_fruit_qty': prod.compensation_last_fruit_qty,
            'compensation_ratio': prod.compensation_ratio,
            })
        return res

    @api.depends('compensation_last_fruit_qty', 'compensation_ratio')
    def _compute_compensation_last_juice_qty(self):
        for wiz in self:
            wiz.compensation_last_juice_qty =\
                wiz.compensation_last_fruit_qty * wiz.compensation_ratio / 100.0

    @api.onchange('compensation_type')
    def compensation_type_change(self):
        pr_oli = self.env['decimal.precision'].precision_get('Fruit Weight')
        pr_ratio = self.env['decimal.precision'].precision_get('Fruit Juice Ratio')
        res = {'warning': {}}
        wh = self.warehouse_id
        if self.compensation_type == 'last':
            today_dt = fields.Date.from_string(fields.Date.context_today(self))
            yesterday = fields.Date.to_string(today_dt - relativedelta(days=1))
            if float_is_zero(self.compensation_last_fruit_qty, precision_digits=pr_oli):
                self.compensation_last_fruit_qty = wh.fruit_compensation_last_qty
            if float_is_zero(self.compensation_ratio, precision_digits=pr_ratio):
                self.compensation_ratio = wh.fruit_juice_compensation_ratio
                last_update = wh.fruit_juice_compensation_ratio_update_date
                if last_update:
                    if last_update < yesterday:
                        res['warning']['message'] = _(
                            "The last update of the compensation ratio for the "
                            "warehouse '%s' took place on %s. You should update "
                            "the compensation ratio on that warehouse.") % (
                                wh.display_name, last_update)
                else:
                    res['warning']['message'] = _(
                        "The field 'Last update of the compensation ratio' is "
                        "empty on the warehouse '%s'.") % wh.display_name
        else:
            self.compensation_last_fruit_qty = 0
            self.compensation_ratio = 0
        return res

    def validate(self):
        self.ensure_one()
        pr_oli = self.env['decimal.precision'].precision_get('Fruit Weight')
        pr_ratio = self.env['decimal.precision'].precision_get('Fruit Juice Ratio')
        prod = self.production_id
        ctype = self.compensation_type
        cloc = self.compensation_location_id
        density = prod.company_id.fruit_juice_density
        compensation_juice_qty = False
        if ctype in ('first', 'last'):
            if not cloc:
                raise UserError(_(
                    "You must select a compensation tank."))
            assert cloc.fruit_tank_type == 'compensation', 'wrong fruit_tank_type'
        if ctype == 'last':
            cratio = self.compensation_ratio
            if float_compare(self.compensation_last_fruit_qty, 0, precision_digits=pr_oli) <= 0:
                raise UserError(_(
                    "For a last-of-day compensation, the fruit compensation "
                    "quantity must be strictly positive."))
            if float_compare(cratio, 0, precision_digits=pr_ratio) <= 0:
                raise UserError(_(
                    "For a last-of-day compensation, the compensation ratio "
                    "must be strictly positive."))
            min_ratio, max_ratio = prod.company_id.fruit_min_max_ratio()
            if cratio < min_ratio or cratio > max_ratio:
                raise UserError(_(
                    "The compensation ratio (%s %%) is not realistic.") % cratio)
            compensation_juice_qty = float_round(
                self.compensation_last_juice_qty, precision_digits=pr_ratio)
        prod.write({
            'compensation_type': ctype,
            'compensation_location_id': cloc.id,
            'compensation_last_fruit_qty': self.compensation_last_fruit_qty,
            'compensation_ratio': self.compensation_ratio,
            'compensation_juice_qty': compensation_juice_qty,
            'compensation_juice_qty_kg': compensation_juice_qty * density,
            })
        return True
