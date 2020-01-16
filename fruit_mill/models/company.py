# Copyright 2018 Barroux Abbey (https://www.barroux.org/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import models, fields, api
import odoo.addons.decimal_precision as dp


class ResCompany(models.Model):
    _inherit = 'res.company'

    fruit_max_qty_per_palox = fields.Integer(
        string='Maximum Quantity of Fruits per Palox', default=500)
    fruit_harvest_arrival_max_delta_days = fields.Integer(
        string='Maximum Delay Between Harvest Start Date and Arrival Date',
        default=3,
        help="If the delay between the harvest start date and the arrival "
        "date is superior to the number of days indicated here, Odoo will "
        "display a warning upon arrival validation when the juice destination "
        "is sale or mix.")
    current_season_id = fields.Many2one(
        'fruit.season', compute='_compute_current_season_id', readonly=True,
        string='Current Season')
    # START APPOINTMENTS
    fruit_appointment_qty_per_palox = fields.Integer(
        string='Quantity of Fruits per Palox', default=380)
    fruit_appointment_arrival_no_leaf_removal_minutes = fields.Integer(
        string='Arrival Appointment Default Duration without Leaf Removal', default=3,
        help="Number of minutes per 100 kg of fruits")
    fruit_appointment_arrival_leaf_removal_minutes = fields.Integer(
        string='Arrival Appointment Default Duration with Leaf Removal', default=8,
        help="Number of minutes per 100 kg of fruits")
    fruit_appointment_arrival_min_minutes = fields.Integer(
        string='Arrival Appointment Minimum Duration', default=5,
        help="Arrival appointment minimum duration in minutes")
    fruit_appointment_lend_minutes = fields.Integer(
        string='Lend Palox/Cases Appointment Default Duration', default=5)
    fruit_appointment_withdrawal_minutes = fields.Integer(
        string='Withdrawal Appointment Default Duration', default=5)
    # END APPOINTMENTS
    fruit_shrinkage_ratio = fields.Float(
        string='Shrinkage Ratio', default=0.4,
        digits=dp.get_precision('Fruit Juice Ratio'))
    fruit_filter_ratio = fields.Float(
        string='Filter Loss Ratio', default=1.0,
        digits=dp.get_precision('Fruit Juice Ratio'))
    fruit_min_ratio = fields.Float(
        string='Minimum Ratio', default=5,
        digits=dp.get_precision('Fruit Juice Ratio'),
        help="A ratio under that value would be considered as not realistic "
        "and would trigger a blocking error message.")
    fruit_max_ratio = fields.Float(
        string='Maximum Ratio', default=35,
        digits=dp.get_precision('Fruit Juice Ratio'),
        help="A ratio above that value would be considered as not realistic "
        "and would trigger a blocking error message.")
    fruit_juice_density = fields.Float(
        string='Fruit Juice Density', default=0.916,
        digits=dp.get_precision('Fruit Juice Density'),
        help='Fruit juice density in kg per liter')
    fruit_juice_leaf_removal_product_id = fields.Many2one(
        'product.product', string='Leaf Removal Product',
        domain=[('fruit_type', '=', 'service')])
    fruit_juice_production_product_id = fields.Many2one(
        'product.product', string='Production Product',
        domain=[('fruit_type', '=', 'service')])
    fruit_juice_tax_product_id = fields.Many2one(
        'product.product', string='AFIDOL Tax Product',
        domain=[('fruit_type', '=', 'tax')])
    fruit_juice_early_bird_discount_product_id = fields.Many2one(
        'product.product', string='Early Bird Discount Product',
        domain=[('fruit_type', '=', 'service')])
    fruit_juice_production_start_hour = fields.Integer(
        string='Default Juice Production Start Hour', default=8)
    fruit_juice_production_start_minute = fields.Integer(
        string='Default Juice Production Start Minute', default=0)
    fruit_juice_production_duration_minutes = fields.Integer(
        string='Default Juice Production Duration', default=30)
    fruit_juice_analysis_default_user_id = fields.Many2one(
        'res.users', string='Default User for Fruit Juice Analysis')
    # fruit_juice_tax_price_unit = fields.Float(
    #    string='AFIDOL Tax Unit Price',
    #    digits=dp.get_precision('Fruit Juice Tax Price Unit'), default=0.129,
    #    help='Tax unit price per liter of fruit juice')

    _sql_constraints = [(
        #'fruit_poll_average_season_count_positive',
        #'CHECK(fruit_poll_average_season_count >= 0)',
       # 'Number of Past Seasons must be positive.'), (
        'fruit_max_qty_per_palox_positive',
        'CHECK(fruit_max_qty_per_palox >= 0)',
        'Maximum Quantity of Fruits per Palox must be positive.'), (
        'fruit_juice_density_positive',
        'CHECK(fruit_juice_density > 0)',
        'Fruit juice density must be strictly positive.'), (
        'fruit_shrinkage_ratio_positive',
        'CHECK(fruit_shrinkage_ratio >= 0)',
        'Shrinkage Ratio must be positive.'), (
        'fruit_filter_ratio_positive',
        'CHECK(fruit_filter_ratio >= 0)',
        'Filter Ratio must be positive.'), (
        'fruit_min_ratio_positive',
        'CHECK(fruit_min_ratio >= 0)',
        'Fruit Min Ratio must be positive.'), (
        'fruit_max_ratio_positive',
        'CHECK(fruit_max_ratio >= 0)',
        'Fruit Max Ratio must be positive.'), (
        'fruit_appointment_qty_per_palox_positive',
        'CHECK(fruit_appointment_qty_per_palox >= 0)',
        'The Quantity of Fruits per Palox must be positive.'), (
        'fruit_appointment_arrival_no_leaf_removal_minutes_positive',
        'CHECK(fruit_appointment_arrival_no_leaf_removal_minutes >= 0)',
        'Arrival Appointment Default Duration without Leaf Removal must be positive.'), (
        'fruit_appointment_arrival_leaf_removal_minutes_positive',
        'CHECK(fruit_appointment_arrival_leaf_removal_minutes >= 0)',
        'Arrival Appointment Default Duration with Leaf Removal must be positive.'), (
        'fruit_appointment_arrival_min_minutes_positive',
        'CHECK(fruit_appointment_arrival_min_minutes >= 0)',
        'Arrival Appointment Minimum Duration must be positive.'), (
        'fruit_appointment_lend_minutes_positive',
        'CHECK(fruit_appointment_lend_minutes >= 0)',
        'Lend Palox/Cases Appointment Default Duration must be positive.'), (
        'fruit_appointment_withdrawal_minutes_positive',
        'CHECK(fruit_appointment_withdrawal_minutes >= 0)',
        'Withdrawal Appointment Default Duration must be positive.'), (
        'fruit_juice_production_start_hour_min',
        'CHECK(fruit_juice_production_start_hour >= 0)',
        'Juice Production Start Hour must be between 0 and 23.'), (
        'fruit_juice_production_start_hour_max',
        'CHECK(fruit_juice_production_start_hour <= 23)',
        'Juice Production Start Hour must be between 0 and 23.'), (
        'fruit_juice_production_start_minute_min',
        'CHECK(fruit_juice_production_start_minute >= 0)',
        'Juice Production Start Minute must be between 0 and 59.'), (
        'fruit_juice_production_start_minute_max',
        'CHECK(fruit_juice_production_start_minute <= 59)',
        'Juice Production Start Minute must be between 0 and 59.'), (
        'fruit_juice_production_duration_minutes_positive',
        'CHECK(fruit_juice_production_duration_minutes >= 0)',
        'Juice Production Duration must be positive.')
        ]

    @api.model
    def fruit_juice_liter2kg(self, qty):
        return qty * self.fruit_juice_density

    @api.model
    def fruit_juice_kg2liter(self, qty):
        return qty * 1.0 / self.fruit_juice_density

    def fruit_min_max_ratio(self):
        self.ensure_one()
        return (self.fruit_min_ratio, self.fruit_max_ratio)

    def get_current_season(self):
        self.ensure_one()
        #import pdb; pdb.set_trace()
        today = fields.Date.context_today(self)
        season = self.env['fruit.season'].search([
            ('start_date', '<=', today),
            ('end_date', '>=', today),
            ('company_id', '=', self.id),
            ], limit=1)
        if season:
            return season
        season = self.env['fruit.season'].search([
            ('year', '=', today[:4]),
            ('company_id', '=', self.id),
            ], limit=1)
        if season:
            return season
        season = self.env['fruit.season'].search([
            ('start_date', '<=', today),
            ('company_id', '=', self.id)],
            order='start_date desc', limit=1)
        return season or False

    def _compute_current_season_id(self):
        for company in self:
            company.current_season_id = company.get_current_season()

    def current_season_update(self, fields_view_get_result, view_type):
        self.ensure_one()
        fields_view_get_result['arch'] = fields_view_get_result['arch'].replace(
            "'CURRENT_SEASON_ID'", str(self.current_season_id.id))
        return fields_view_get_result
