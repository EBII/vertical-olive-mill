# Copyright 2018 Barroux Abbey (https://www.barroux.org/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta
import logging
logger = logging.getLogger(__name__)


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    fruit_mill = fields.Boolean(string='Fruit Mill')
    fruit_regular_case_total = fields.Integer(string='Regular Cases Total')
    fruit_regular_case_stock = fields.Integer(
        compute='_compute_cases', string='Regular Cases in Stock',
        readonly=True)
    fruit_organic_case_total = fields.Integer(string='Organic Cases Total')
    fruit_organic_case_stock = fields.Integer(
        compute='_compute_cases', string='Organic Cases in Stock',
        readonly=True)
    fruit_withdrawal_loc_id = fields.Many2one(
        'stock.location', string='Fruit Juice Withdrawal Location',
        domain=[('fruit_tank_type', '=', False), ('usage', '=', 'internal')])
    fruit_compensation_loc_id = fields.Many2one(
        'stock.location', string='Fruit Juice Compensation Tank',
        domain=[('fruit_tank_type', '=', 'compensation')])
    fruit_compensation_last_qty = fields.Float(
        string='Fruit Compensation Quantity', default=45.0,
        digits=dp.get_precision('Fruit Weight'))
    fruit_juice_compensation_ratio = fields.Float(
        string='Compensation Ratio',
        digits=dp.get_precision('Fruit Juice Ratio'), default=17)
    fruit_juice_compensation_ratio_update_date = fields.Date(
        string='Last Update of the Compensation Ratio')
    fruit_juice_compensation_ratio_days = fields.Integer(
        string='Base for Compensation Ratio Computation', default=7)

    _sql_constraints = [(
        'fruit_juice_compensation_ratio_positive',
        'CHECK(fruit_juice_compensation_ratio >= 0)',
        'Juice compensation ratio must be positive or null.'),
        ('fruit_compensation_last_qty_positive',
         'CHECK(fruit_compensation_last_qty >= 0)',
         'Fruit Compensation Quantity must be positive or null.')]

    @api.depends('fruit_organic_case_total', 'fruit_regular_case_total')
    def _compute_cases(self):
        cases_res = self.env['fruit.lended.case'].read_group(
            [('warehouse_id', 'in', self.ids)],
            ['warehouse_id', 'regular_qty', 'organic_qty'], ['warehouse_id'])
        if cases_res:
            for cases_re in cases_res:
                wh = self.browse(cases_re['warehouse_id'][0])
                wh.fruit_regular_case_stock =\
                    wh.fruit_regular_case_total - cases_re['regular_qty']
                wh.fruit_organic_case_stock =\
                    wh.fruit_organic_case_total - cases_re['organic_qty']
        else:
            for wh in self:
                wh.fruit_regular_case_stock = wh.fruit_regular_case_total
                wh.fruit_organic_case_stock = wh.fruit_organic_case_total

    @api.model
    def fruit_juice_compensation_ratio_update_cron(self):
        logger.info('Starting juice compensation ratio update cron')
        for wh in self.search([('fruit_mill', '=', True)]):
            wh.fruit_juice_compensation_ratio_update()

    def fruit_juice_compensation_ratio_update(self):
        today = fields.Date.context_today(self)
        today_dt = fields.Date.from_string(today)
        if not self.fruit_mill:
            return
        start_date_dt = today_dt - relativedelta(
            days=self.fruit_juice_compensation_ratio_days)
        start_date = fields.Date.to_string(start_date_dt)
        rg = self.env['fruit.arrival.line'].read_group([
            ('production_state', '=', 'done'),
            ('production_date', '<=', today),
            ('production_date', '>=', start_date),
            ], ['fruit_qty', 'juice_qty'], [])
        if rg and rg[0]['fruit_qty']:
            ratio = 100 * rg[0]['juice_qty'] / rg[0]['fruit_qty']
            self.write({
                'fruit_juice_compensation_ratio_update_date': today,
                'fruit_juice_compensation_ratio': ratio,
                })
            logger.info(
                'Juice compensation ratio updated to %s on warehouse %s '
                'start_date %s ', ratio, self.name, start_date)
        else:
            logger.warning(
                'Juice compensation ratio not updated on warehouse %s '
                'because there is no production data between %s and %s',
                self.name, start_date, today)

    def fruit_get_shrinkage_tank(self, juice_product, raise_if_not_found=True):
        self.ensure_one()
        assert juice_product, 'juice_product is a required arg'
        sloc = self.env['stock.location'].search([
            ('fruit_tank_type', '=', 'shrinkage'),
            ('id', 'child_of', self.view_location_id.id),
            ('fruit_shrinkage_juice_product_ids', '=', juice_product.id)],
            limit=1)
        if not sloc and raise_if_not_found:
            raise UserError(_(
                "Could not find a shrinkage tank in warehouse '%s' "
                "that accepts '%s'.") % (
                    self.display_name, juice_product.name))
        return sloc or False
