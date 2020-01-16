# Copyright 2019 Barroux Abbey (http://www.barroux.org/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
import odoo.addons.decimal_precision as dp
from odoo.tools import float_compare, float_is_zero


class FruitPreseasonPoll(models.Model):
    _name = 'fruit.preseason.poll'
    _description = 'Pre-season polls'
    _order = 'season_id desc, id desc'

    company_id = fields.Many2one(
        'res.company', string='Company',
        ondelete='cascade', required=True,
        default=lambda self: self.env['res.company']._company_default_get())
    season_id = fields.Many2one(
        'fruit.season', string='Season', required=True, index=True,
        default=lambda self: self.env.user.company_id.current_season_id.id)
    partner_id = fields.Many2one(
        'res.partner', string='Fruit Farmer', required=True, index=True,
        domain=[('parent_id', '=', False), ('fruit_farmer', '=', True)])
    fruit_culture_type = fields.Selection(
        related='partner_id.commercial_partner_id.fruit_culture_type', readonly=True)
    commercial_partner_id = fields.Many2one(
        related='partner_id.commercial_partner_id', readonly=True, store=True)
    fruit_organic_certified_logo = fields.Binary(
        related='partner_id.commercial_partner_id.fruit_organic_certified_logo',
        readonly=True)
    line_ids = fields.One2many(
        'fruit.preseason.poll.line', 'poll_id', string='Lines')
    past_data_ok = fields.Boolean(readonly=True)
    n1_season_id = fields.Many2one(
        'fruit.season', readonly=True, string='N-1 Season')
    n1_ratio_net = fields.Float(
        string='N-1 Net Ratio (%)',
        digits=dp.get_precision('Fruit Juice Ratio'), readonly=True)
    n1_fruit_qty = fields.Integer(
        string='N-1 Fruit Qty (kg)', readonly=True)
    n1_juice_qty_net = fields.Integer(
        string='N-1 Net Juice Qty (L)', readonly=True)
    n1_sale_fruit_qty = fields.Integer(
        string='N-1 Sale Fruit Qty (kg)', readonly=True)
    n1_sale_juice_qty = fields.Integer(
        string='N-1 Sale Juice Qty (L)', readonly=True)
    n2_season_id = fields.Many2one(
        'fruit.season', readonly=True, string='N-2 Season')
    n2_ratio_net = fields.Float(
        string='N-2 Net Ratio (%)',
        digits=dp.get_precision('Fruit Juice Ratio'), readonly=True)
    n2_fruit_qty = fields.Integer(
        string='N-2 Fruit Qty (kg)', readonly=True)
    n2_juice_qty_net = fields.Integer(
        string='N-2 Net Juice Qty (L)', readonly=True)
    n2_sale_fruit_qty = fields.Integer(
        string='N-2 Sale Fruit Qty (kg)', readonly=True)
    n2_sale_juice_qty = fields.Integer(
        string='N-2 Sale Juice Qty (L)', readonly=True)
    n3_season_id = fields.Many2one(
        'fruit.season', readonly=True, string='N-3 Season')
    n3_ratio_net = fields.Float(
        string='N-3 Net Ratio (%)',
        digits=dp.get_precision('Fruit Juice Ratio'), readonly=True)
    n3_fruit_qty = fields.Integer(
        string='N-3 Fruit Qty (kg)', readonly=True)
    n3_juice_qty_net = fields.Integer(
        string='N-3 Net Juice Qty (L)', readonly=True)
    n3_sale_fruit_qty = fields.Integer(
        string='N-3 Sale Fruit Qty (kg)', readonly=True)
    n3_sale_juice_qty = fields.Integer(
        string='N-3 Sale Juice Qty (L)', readonly=True)
    past_average_ratio_net = fields.Float(
        digits=dp.get_precision('Fruit Juice Ratio'), readonly=True,
        string='Past Average Net Ratio (%)')
    past_average_fruit_qty = fields.Integer(
        string='Past Average Fruit Qty (kg)', readonly=True)
    past_average_juice_qty_net = fields.Integer(
        string='Past Average Net Juice Qty (L)', readonly=True)
    past_average_sale_fruit_qty = fields.Integer(
        string='Past Average Sale Fruit Qty (kg)', readonly=True)
    past_average_sale_juice_qty = fields.Integer(
        string='Past Average Sale Juice Qty (L)', readonly=True)

    _sql_constraints = [(
        'partner_season_unique',
        'unique(partner_id, season_id)',
        'There is already a poll for this fruit farmer for the same season.')]

    @api.depends('past_average_ratio', 'fruit_qty', 'sale_fruit_qty')
    def _compute_juice_qty(self):
        for poll in self:
            # TODO when poll.past_average_ratio is null because there is no past
            poll.juice_qty = poll.fruit_qty * poll.past_average_ratio / 100.0
            poll.sale_juice_qty = poll.sale_fruit_qty * poll.past_average_ratio / 100.0

    @api.onchange('partner_id')
    def partner_id_change(self):
        if self.partner_id and self.past_data_ok:
            self.past_data_ok = False

    def update_past_data(self):
        self.ensure_one()
        oso = self.env['fruit.season']
        prec = self.env['decimal.precision'].precision_get('Fruit Weight')
        vals = {
            'past_data_ok': True,
            'past_average_ratio_net': 0.0,
            'past_average_fruit_qty': 0.0,
            'past_average_juice_qty_net': 0.0,
            'past_average_sale_juice_qty': 0.0,
            'past_average_sale_fruit_qty': 0.0,
            }
        season = self.season_id
        company = self.company_id
        for i in ['n1', 'n2', 'n3']:
            for suffix in ['season_id', 'ratio_net', 'fruit_qty', 'juice_qty_net', 'sale_fruit_qty', 'sale_juice_qty']:
                field_name = '%s_%s' % (i, suffix)
                vals[field_name] = False
        past_seasons = self.env['fruit.season'].search([
            ('company_id', '=', company.id),
            ('start_date', '<', season.start_date),
            ], order='start_date desc', limit=3)
        res = self.env['fruit.arrival.line'].read_group([
            ('season_id', 'in', past_seasons.ids),
            ('state', '=', 'done'),
            ('production_state', '=', 'done'),
            ('commercial_partner_id', '=', self.commercial_partner_id.id)],
            ['fruit_qty', 'juice_qty_net', 'sale_juice_qty', 'season_id'],
            ['season_id'])
        print("res=", res)
        season2data = {}
        for re in res:
            season_id = re['season_id'][0]
            season = oso.browse(season_id)
            if not float_is_zero(re['fruit_qty'], precision_digits=prec):
                season2data[season] = {
                    'fruit_qty': re['fruit_qty'],
                    'sale_juice_qty': re['sale_juice_qty'],
                    'juice_qty_net': re['juice_qty_net'],
                    }
        # caution: an fruit farmer may not have arrivals during each season
        # We do the average on the seasons where he made at least 1 arrival
        season_count = 0
        i = 0
        for season in past_seasons:
            i += 1
            prefix = 'n%d_' % i
            vals[prefix + 'season_id'] = season.id
            if season in season2data:
                season_count += 1
                for field_name in ['fruit_qty', 'juice_qty_net', 'sale_juice_qty']:
                    vals[prefix + field_name] = season2data[season][field_name]
                    vals['past_average_' + field_name] += season2data[season][field_name]
                vals[prefix + 'ratio_net'] = 100 * vals[prefix + 'juice_qty_net'] / vals[prefix + 'fruit_qty']
                if vals[prefix + 'ratio_net'] > 0:
                    vals[prefix + 'sale_fruit_qty'] = vals[prefix + 'sale_juice_qty'] * 100 / vals[prefix + 'ratio_net']
        # Finalize average computation
        if season_count:
            vals['past_average_ratio_net'] = 100 * vals['past_average_juice_qty_net'] / vals['past_average_fruit_qty']
            if vals['past_average_ratio_net'] > 0:
                vals['past_average_sale_fruit_qty'] = vals['past_average_sale_juice_qty'] * 100 / vals['past_average_ratio_net']
            vals['past_average_fruit_qty'] = vals['past_average_fruit_qty'] / season_count
            vals['past_average_juice_qty_net'] = vals['past_average_juice_qty_net'] / season_count
            vals['past_average_sale_juice_qty'] = vals['past_average_sale_juice_qty'] / season_count
        self.write(vals)

    @api.depends('partner_id', 'season_id')
    def name_get(self):
        res = []
        for rec in self:
            name = '%s - %s' % (rec.season_id.name, rec.partner_id.display_name)
            res.append((rec.id, name))
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(FruitPreseasonPoll, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        return self.env.user.company_id.current_season_update(res, view_type)


class FruitPreseasonPollLine(models.Model):
    _name = 'fruit.preseason.poll.line'
    _description = 'Pre-season polls Line'

    poll_id = fields.Many2one(
        'fruit.preseason.poll', string='Pre-Season Poll', ondelete='cascade')
    fruit_qty = fields.Integer(
        string='Fruit Qty (kg)', required=True)
    juice_product_id = fields.Many2one(
        'product.product', string='Juice Type', index=True,
        domain=[('fruit_type', '=', 'juice')])
    sale_fruit_qty = fields.Integer(
        string='Sale Fruit Qty (kg)', required=True)
    juice_qty = fields.Integer(
        string='Juice Qty (L)', store=True,
        compute='_compute_juice_qty', inverse='_inverse_juice_qty')
    sale_juice_qty = fields.Integer(
        string='Sale Juice Qty (L)', store=True,
        compute='_compute_sale_juice_qty', inverse='_inverse_sale_juice_qty')
    fruit_culture_type = fields.Selection(
        related='poll_id.partner_id.commercial_partner_id.fruit_culture_type', readonly=True)
    commercial_partner_id = fields.Many2one(
        related='poll_id.partner_id.commercial_partner_id', store=True,
        string='Fruit Farmer')
    season_id = fields.Many2one(related='poll_id.season_id', store=True)

    _sql_constraints = [(
        'partner_season_juice_product_unique',
        'unique(commercial_partner_id, season_id, juice_product_id)',
        'Same juice type selected twice.'
        ), (
        'sale_inferior',
        'CHECK(fruit_qty - sale_fruit_qty >= 0)',
        'The sale fruit quantity cannot be superior to the fruit quantity.'
        )]



    @api.depends('fruit_qty')
    def _compute_juice_qty(self):
        for line in self:
            line.juice_qty = int(line.fruit_qty * line.poll_id.past_average_ratio_net / 100)

    @api.onchange('juice_qty')
    def _inverse_juice_qty(self):
        for line in self:
            if line.poll_id.past_average_ratio_net > 0:
                line.fruit_qty = int(100 * line.juice_qty / line.poll_id.past_average_ratio_net)
            else:
                line.fruit_qty = 0

    @api.depends('sale_fruit_qty')
    def _compute_sale_juice_qty(self):
        for line in self:
            line.sale_juice_qty = int(line.sale_fruit_qty * line.poll_id.past_average_ratio_net / 100)

    @api.onchange('sale_juice_qty')
    def _inverse_sale_juice_qty(self):
        for line in self:
            if line.poll_id.past_average_ratio_net > 0:
                line.sale_fruit_qty = int(100 * line.sale_juice_qty / line.poll_id.past_average_ratio_net)
            else:
                line.sale_fruit_qty = 0

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(FruitPreseasonPollLine, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        return self.env.user.company_id.current_season_update(res, view_type)
