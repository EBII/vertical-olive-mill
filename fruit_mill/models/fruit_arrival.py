# Copyright 2018 Barroux Abbey (https://www.barroux.org/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero, float_round
from odoo.tools.misc import formatLang
from babel.dates import format_date
import odoo.addons.decimal_precision as dp


class FruitArrival(models.Model):
    _name = 'fruit.arrival'
    _description = 'Fruit Arrival'
    _order = 'name desc'
    _inherit = ['mail.thread']

    name = fields.Char(string='Arrival Number', required=True, default='/')
    company_id = fields.Many2one(
        'res.company', string='Company',
        ondelete='cascade', required=True,
        states={'done': [('readonly', True)]},
        default=lambda self: self.env['res.company']._company_default_get())
    season_id = fields.Many2one(
        'fruit.season', string='Season', required=True, index=True,
        default=lambda self: self.env.user.company_id.current_season_id.id,
        states={'done': [('readonly', True)]}, ondelete='restrict')
    partner_id = fields.Many2one(
        'res.partner', string='Fruit Farmer', required=True, index=True,
        domain=[('parent_id', '=', False), ('fruit_farmer', '=', True)],
        states={'done': [('readonly', True)]}, ondelete='restrict',
        track_visibility='onchange')
    commercial_partner_id = fields.Many2one(
        related='partner_id.commercial_partner_id', readonly=True, store=True)
    fruit_organic_certified_logo = fields.Binary(
        related='partner_id.commercial_partner_id.fruit_organic_certified_logo',
        readonly=True)
    fruit_culture_type = fields.Selection(
        related='partner_id.commercial_partner_id.fruit_culture_type', readonly=True)
    fruit_cultivation_form_ko = fields.Boolean(
        related='partner_id.commercial_partner_id.fruit_cultivation_form_ko',
        readonly=True)
    fruit_parcel_ko = fields.Boolean(
        related='partner_id.commercial_partner_id.fruit_parcel_ko', readonly=True)
    fruit_organic_certif_ko = fields.Boolean(
        related='partner_id.commercial_partner_id.fruit_organic_certif_ko',
        readonly=True)
    partner_fruit_tree_total = fields.Integer(
        related='partner_id.commercial_partner_id.fruit_tree_total',
        readonly=True)
    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Warehouse', required=True, index=True,
        domain=[('fruit_mill', '=', True)],
        default=lambda self: self.env.user._default_fruit_mill_wh(),
        states={'done': [('readonly', True)]},
        track_visibility='onchange')
    default_variant_id = fields.Many2one(
        'fruit.variant', string='Default Fruit Variant',
        states={'done': [('readonly', True)]})
    default_ochard_id = fields.Many2one(
        'fruit.ochard', string='Default Ochard',
        states={'done': [('readonly', True)]})
    default_leaf_removal = fields.Boolean(
        string='Default Leaf Removal',
        states={'done': [('readonly', True)]})
    fruit_qty = fields.Float(
        compute='_compute_fruit_qty', readonly=True, store=True,
        track_visibility='onchange', string='Total Quantity (kg)',
        digits=dp.get_precision('Fruit Weight'),
        help="Total fruit quantity in kg")
    default_juice_destination = fields.Selection([
        ('withdrawal', 'Withdrawal'),
        ('sale', 'Sale'),
        ('mix', 'Mix'),
        ], string='Default Juice Destination',
        states={'done': [('readonly', True)]})
    default_juice_product_id = fields.Many2one(
        'product.product', string='Default Juice Type',
        domain=[('fruit_type', '=', 'juice')],
        states={'done': [('readonly', True)]})
    state = fields.Selection([
        ('draft', 'Draft'),
        ('weighted', 'Weighted'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ], string='State', default='draft', readonly=True,
        track_visibility='onchange')
    date = fields.Date(
        string='Arrival Date', track_visibility='onchange',
        default=fields.Date.context_today, required=True,
        states={'done': [('readonly', True)]})
    harvest_start_date = fields.Date(
        string='Harvest Start Date', required=True,
        states={'done': [('readonly', True)]})
    done_datetime = fields.Datetime(string='Date Done', readonly=True)
    line_ids = fields.One2many(
        'fruit.arrival.line', 'arrival_id', string='Arrival Lines',
        states={'done': [('readonly', True)]})
    returned_regular_case = fields.Integer(
        string='Returned Regular Cases', states={'done': [('readonly', True)]})
    returned_organic_case = fields.Integer(
        string='Returned Organic Cases', states={'done': [('readonly', True)]})
    lended_case_id = fields.Many2one(
        'fruit.lended.case', string='Returned Lended Cases Move', readonly=True)
    hide_lend_palox_case_button = fields.Boolean(
        string='Hide Button Lend Palox and/or Cases', readonly=True)
    returned_palox_ids = fields.Many2many(
        'fruit.palox', string='Other Returned Palox',
        states={'done': [('readonly', True)]},
        help="Select returned palox other than those used in the arrival "
        "lines")
    fruit_qty_pressed = fields.Float(
        string='Fruit Qty Pressed (kg)',
        digits=dp.get_precision('Fruit Weight'), readonly=True)
    juice_qty_net = fields.Float(
        string='Net Juice Qty (L)',
        readonly=True, digits=dp.get_precision('Fruit Juice Volume'),
        help="Net juice quantity produced in liters."
        "\nFirst-of-day compensation: included."
        "\nLast-of-day compensation: already deducted."
        "\nShrinkage: already deducted."
        "\nFilter loss: already deducted.")
    juice_ratio_net = fields.Float(
        string='Juice Net Ratio (% L)', digits=dp.get_precision('Fruit Juice Ratio'),
        readonly=True, group_operator='avg')
    fruit_ratio_net = fields.Float(
        string='Fruit Net Ratio (kg / L)', digits=(16, 2),
        readonly=True, group_operator='avg')
    lended_regular_case = fields.Integer(
        compute='_compute_lended_case', string='Lended Regular Case', readonly=True)
    lended_organic_case = fields.Integer(
        compute='_compute_lended_case', string='Lended Organic Case', readonly=True)
    lended_palox = fields.Integer(
        compute='_compute_lended_palox', string='Lended Palox', readonly=True)
    operator_user_id = fields.Many2one(
        'res.users', string='Operator', domain=[('fruit_operator', '=', True)],
        ondelete='restrict', copy=False)

    _sql_constraints = [(
        'returned_regular_case_positive',
        'CHECK(returned_regular_case >= 0)',
        'The returned regular cases must be positive or null.'), (
        'returned_organic_case_positive',
        'CHECK(returned_organic_case >= 0)',
        'The returned organic cases must be positive or null.')]

    @api.depends('line_ids.fruit_qty')
    def _compute_fruit_qty(self):
        res = self.env['fruit.arrival.line'].read_group(
            [('arrival_id', 'in', self.ids)],
            ['arrival_id', 'fruit_qty'], ['arrival_id'])
        for re in res:
            self.browse(re['arrival_id'][0]).fruit_qty = re['fruit_qty']

    @api.depends(
        'returned_regular_case', 'returned_organic_case', 'lended_case_id')
    def _compute_lended_case(self):
        olco = self.env['fruit.lended.case']
        for arrival in self:
            cases_res = olco.read_group([
                ('company_id', '=', arrival.company_id.id),
                ('partner_id', '=', arrival.commercial_partner_id.id)],
                ['regular_qty', 'organic_qty'], [])
            lended_regular_case = cases_res and cases_res[0]['regular_qty'] or 0
            lended_organic_case = cases_res and cases_res[0]['organic_qty'] or 0
            if not arrival.lended_case_id:
                lended_regular_case -= arrival.returned_regular_case
                lended_organic_case -= arrival.returned_organic_case
            arrival.lended_regular_case = lended_regular_case
            arrival.lended_organic_case = lended_organic_case

    @api.depends('returned_palox_ids', 'line_ids.palox_id')
    def _compute_lended_palox(self):
        opo = self.env['fruit.palox']
        for arrival in self:
            lended_palox = opo.search([
                ('borrower_partner_id', '=', arrival.commercial_partner_id.id)])
            if arrival.state in ('draft', 'weighted'):
                for rp in arrival.returned_palox_ids:
                    if rp in lended_palox:
                        lended_palox -= rp
                for line in arrival.line_ids:
                    if line.palox_id in lended_palox:
                        lended_palox -= line.palox_id
            arrival.lended_palox = len(lended_palox)

    @api.constrains('date', 'harvest_start_date')
    def arrival_check(self):
        for arrival in self:
            if arrival.harvest_start_date > arrival.date:
                raise ValidationError(_(
                    "On arrival %s, the harvest start date (%s) cannot be "
                    "after the arrival date (%s)!") % (
                        arrival.name, arrival.harvest_start_date,
                        arrival.date))

    @api.onchange('partner_id')
    def partner_id_change(self):
        if self.partner_id:
            ochards = self.env['fruit.ochard'].search([
                ('partner_id', '=', self.commercial_partner_id.id)])
            if len(ochards) == 1:
                self.default_ochard_id = ochards
        else:
            self.default_ochard_id = False

    @api.onchange('default_ochard_id')
    def default_ochard_id_change(self):
        if self.default_ochard_id:
            ochard = self.default_ochard_id
            if len(ochard.parcel_ids) == 1 and len(ochard.parcel_ids[0].variant_ids) == 1:
                self.default_variant_id = ochard.parcel_ids[0].variant_ids[0]

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'fruit.arrival')
        return super(FruitArrival, self).create(vals)

    def cancel(self):
        for arrival in self:
            if all([line.production_id for line in arrival.line_ids]):
                raise UserError(_(
                    "Cannot cancel arrival %s because all its lines are "
                    "currently selected in productions.") % arrival.name)
            arrival.line_ids.filtered(
                lambda l: not l.production_id).write({'state': 'cancel'})
        self.write({'state': 'cancel'})

    def back2draft(self):
        for arrival in self:
            assert arrival.state == 'cancel'
            arrival.line_ids.filtered(
                lambda l: l.state == 'cancel').write({'state': 'draft'})
        self.write({'state': 'draft'})

    def check_arrival(self):
        warn_msgs = []
        oalo = self.env['fruit.arrival.line']
        pr_oli = self.env['decimal.precision'].precision_get('Fruit Weight')
        pr_juice = self.env['decimal.precision'].precision_get(
            'Fruit Juice Volume')
        wh = self.warehouse_id
        fruit_culture_type = self.commercial_partner_id.fruit_culture_type
        if self.returned_regular_case or self.returned_organic_case:
            if (
                    not self.lended_case_id and
                    self.returned_regular_case > self.commercial_partner_id.fruit_lended_regular_case):
                raise UserError(_(
                    "The fruit farmer '%s' currently has %d lended case(s) "
                    "but the fruit arrival %s declares %d returned case(s).")
                    % (self.commercial_partner_id.display_name,
                       self.commercial_partner_id.fruit_lended_regular_case,
                       self.name,
                       self.returned_regular_case))
            if (
                    not self.lended_case_id and
                    self.returned_organic_case >
                    self.commercial_partner_id.fruit_lended_organic_case):
                raise UserError(_(
                    "The fruit farmer '%s' currently has %d lended organic "
                    "case(s) but the fruit arrival %s declares %d returned "
                    "organic case(s).") % (
                        self.commercial_partner_id.display_name,
                        self.commercial_partner_id.fruit_lended_organic_case,
                        self.name,
                        self.returned_organic_case))

        palox_max_weight = self.company_id.fruit_max_qty_per_palox
        has_sale_or_mix = False
        i = 0
        for line in self.line_ids:
            i += 1
            if line.juice_destination in ('sale', 'mix'):
                has_sale_or_mix = True
            if float_is_zero(line.fruit_qty, precision_digits=pr_oli):
                raise UserError(_(
                    "On arrival line number %d, the fruit quantity is null.")
                    % i)

            # Block if juice_product is not coherent with partner (organic, ...)
            if (line.juice_product_id.fruit_culture_type !=
                    fruit_culture_type):
                raise UserError(_(
                    "On arrival line number %d, the destination juice '%s' is "
                    "'%s' but the farmer '%s' is '%s'.") % (
                        i,
                        line.juice_product_id.name,
                        line.juice_product_id.fruit_culture_type,
                        self.commercial_partner_id.display_name,
                        fruit_culture_type,
                        ))
            if (
                    line.juice_destination == 'mix' and
                    float_is_zero(
                        line.mix_withdrawal_juice_qty, precision_digits=pr_juice)):
                raise UserError(_(
                    "On arrival line number %d, the juice destination is 'mix' "
                    "so you must enter the requested withdrawal qty") % i)

            # Check juice product is the same
            if not line.palox_id.juice_product_id:
                line.sudo().palox_id.juice_product_id = line.juice_product_id.id
            elif line.palox_id.juice_product_id != line.juice_product_id:
                raise UserError(_(
                    "You are collecting %s in palox %s but this palox "
                    "currently has %s.") % (
                        line.juice_product_id.name,
                        line.palox_id.name,
                        line.palox_id.juice_product_id.name))

            # Warn palox max qty
            new_weight = line.palox_id.weight + line.fruit_qty
            if new_weight > palox_max_weight:
                raise UserError(_(
                    "With this arrival, the palox %s would weight %s kg, "
                    "which is over the maximum weight for a palox "
                    "(%s kg).") % (
                        line.palox_id.name, new_weight, palox_max_weight))

            if (
                    line.juice_destination == 'mix' and
                    line.mix_withdrawal_juice_qty > wh.fruit_juice_compensation_ratio * line.fruit_qty / 100.0):
                warn_msgs.append(_(
                    "On arrival line number %d that has a mixed juice "
                    "destination, the requested withdraway quantity "
                    "(%s L) is superior to the fruit quantity of the "
                    "line (%s kg) multiplied by the average ratio "
                    "(%s %%).") % (
                        i, line.mix_withdrawal_juice_qty,
                        line.fruit_qty, wh.fruit_juice_compensation_ratio))

            # Warn if not same variant
            same_palox_different_variant = oalo.search([
                ('palox_id', '=', line.palox_id.id),
                ('state', '=', 'done'),
                ('production_id', '=', False),
                ('variant_id', '!=', line.variant_id.id)])
            if same_palox_different_variant:
                warn_msgs.append(_(
                    "You are putting %s in palox %s but arrival line %s "
                    "in the same palox has %s.") % (
                        line.variant_id.display_name,
                        line.palox_id.name,
                        same_palox_different_variant[0].name,
                        same_palox_different_variant[0].variant_id.name))

            # Warn if not same juice destination
            same_palox_different_juice_destination = oalo.search([
                ('palox_id', '=', line.palox_id.id),
                ('state', '=', 'done'),
                ('production_id', '=', False),
                ('juice_destination', '!=', line.juice_destination)])
            if same_palox_different_juice_destination:
                fg = dict(oalo.fields_get(
                    'juice_destination', 'selection')['juice_destination']['selection'])
                warn_msgs.append(_(
                    "You selected '%s' for palox %s but arrival line %s in "
                    "the same palox has '%s'.") % (
                        fg[line.juice_destination],
                        line.palox_id.name,
                        same_palox_different_juice_destination[0].display_name,
                        fg[same_palox_different_juice_destination[0].juice_destination]))
            line.check_arrival_line_hook(i, warn_msgs)
        # for mix/sale, warn if delay between harvest and arrival is too long
        arrival_date_dt = fields.Date.from_string(self.date)
        harvest_st_date_dt = fields.Date.from_string(self.harvest_start_date)
        delta_days = (arrival_date_dt - harvest_st_date_dt).days
        max_delta_days = self.company_id.fruit_harvest_arrival_max_delta_days
        if has_sale_or_mix and delta_days > max_delta_days:
            warn_msgs.append(_(
                "This arrival has sale or mix juice destination and the delay "
                "between the harvest start date (%s) and the arrival date "
                "(%s) is %d days (maximum allowed is %d days).") % (
                    self.harvest_start_date, self.date,
                    delta_days, max_delta_days))
        action = {}
        if warn_msgs:
            action = self.env.ref('fruit_mill.fruit_arrival_warning_action').read()[0]
            action['context'] = {
                'default_arrival_id': self.id,
                'default_msg': '\n\n'.join(warn_msgs),
                'default_count': len(warn_msgs),
                }
        return warn_msgs, action

    def check(self):
        self.ensure_one()
        warn_msgs, action = self.check_arrival()
        return action

    def weighted(self):
        self.ensure_one()
        self.write({'state': 'weighted'})
        return self.check()

    def validate(self):
        self.ensure_one()
        assert self.state in ('draft', 'weighted')
        olco = self.env['fruit.lended.case']
        if not self.line_ids:
            raise UserError(_(
                "Missing lines on arrival '%s'.") % self.name)
        ooao = self.env['fruit.juice.analysis']
        warn_msgs, action = self.check_arrival()
        if warn_msgs:
            if not self._context.get('fruit_no_warning'):
                action['context']['default_show_validation_button'] = True
                return action
            else:
                for warn_msg in warn_msgs:
                    self.message_post(warn_msg)

        arrival_vals = {
            'state': 'done',
            'done_datetime': fields.Datetime.now(),
            }
        i = 0
        for line in self.line_ids:
            i += 1
            if line.palox_id.borrower_partner_id:
                line.palox_id.return_borrowed_palox()
            for palox in self.returned_palox_ids:
                if palox.borrower_partner_id:
                    palox.return_borrowed_palox()
            # Create analysis
            ana_products = self.env['product.product']
            for extra in line.extra_ids.filtered(lambda x: x.product_id.fruit_type == 'analysis'):
                ana_products |= extra.product_id
            if ana_products:
                existing_ana = ooao.search(
                    [('arrival_line_id', '=', line.id)], limit=1)
                if not existing_ana:
                    ana_vals = {
                        'juice_source_type': 'arrival',
                        'arrival_line_id': line.id,
                        'line_ids': [],
                        'season_id': self.season_id.id,
                        'juice_product_id': line.juice_product_id.id,
                        }
                    for ana_product in ana_products:
                        ana_vals['line_ids'].append((0, 0, {'product_id': ana_product.id}))
                    ooao.create(ana_vals)

            # Set line number
            line.write({
                'name': '%s/%s' % (self.name, i),
                })

        if self.returned_regular_case or self.returned_organic_case:
            lended_case_vals = {
                'partner_id': self.commercial_partner_id.id,
                'regular_qty': self.returned_regular_case * -1,
                'organic_qty': self.returned_organic_case * -1,
                'warehouse_id': self.warehouse_id.id,
                'company_id': self.company_id.id,
                'notes': self.name,
                }
            if self.lended_case_id:
                self.lended_case_id.write(lended_case_vals)
            else:
                lended_case = olco.create(lended_case_vals)
                arrival_vals['lended_case_id'] = lended_case.id
        self.write(arrival_vals)
        self.line_ids.write({'state': 'done'})

    def unlink(self):
        for arrival in self:
            if any([l.state == 'done' for l in arrival.line_ids]):
                raise UserError(_(
                    "Cannot delete arrival %s which has some lines in 'Done' state.")
                    % arrival.name)
        return super(FruitArrival, self).unlink()

    def print_report(self):
        self.ensure_one()
        action = self.env['report'].get_action(self, 'fruit.arrival')
        return action

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(FruitArrival, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        return self.env.user.company_id.current_season_update(res, view_type)


class FruitArrivalLine(models.Model):
    _name = 'fruit.arrival.line'
    _description = 'Fruit Arrival Line'
    # TODO STRANGE odoo doesn't take _order into account !
    # it seems it is because arrival_id is a M2O...
    _order = 'arrival_id desc, id'

    name = fields.Char(
        string='Arrival Line Number', required=True, readonly=True,
        default='/')
    # The "state" field cannot be a related field because we want to be able to
    # "partially" cancel an arrival
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
        ], required=True, readonly=True, default='draft', string="State")
    arrival_id = fields.Many2one(
        'fruit.arrival', string='Arrival', ondelete='cascade',
        states={'done': [('readonly', True)]})
    # START RELATED fields for arrival
    company_id = fields.Many2one(
        related='arrival_id.company_id', store=True, readonly=True)
    arrival_state = fields.Selection(
        related='arrival_id.state', string='Arrival State',
        readonly=True, store=True)
    arrival_date = fields.Date(
        related='arrival_id.date', readonly=True, store=True)
    season_id = fields.Many2one(
        related='arrival_id.season_id', readonly=True, store=True, index=True)
    warehouse_id = fields.Many2one(
        related='arrival_id.warehouse_id', readonly=True, store=True, index=True)
    commercial_partner_id = fields.Many2one(
        related='arrival_id.partner_id.commercial_partner_id',
        string='Fruit Farmer', readonly=True, store=True, index=True)
    fruit_culture_type = fields.Selection(
        related='arrival_id.partner_id.commercial_partner_id.fruit_culture_type',
        readonly=True, store=True)
    # END RELATED fields for arrival
    leaf_removal = fields.Boolean(
        string='Leaf Removal', states={'done': [('readonly', True)]})
    variant_id = fields.Many2one(
        'fruit.variant', string='Fruit Variant', required=True,
        ondelete='restrict', states={'done': [('readonly', True)]})
    palox_weight = fields.Float(
        string='Gross Palox Weight', digits=dp.get_precision('Fruit Weight'),
        help="If you enter the gross palox weight, Odoo will use the palox "
        "empty weight to set the fruit quantity.",
        states={'done': [('readonly', True)]})
    fruit_qty = fields.Float(
        string='Fruit Qty (kg)', required=True,
        digits=dp.get_precision('Fruit Weight'),
        states={'done': [('readonly', True)]},
        help="Fruit quantity in kg."
        "\nFirst-of-day compensation: not included."
        "\nLast-of-day compensation: not deducted.")
    ochard_id = fields.Many2one(
        'fruit.ochard', string='Ochard', required=True, ondelete='restrict',
        states={'done': [('readonly', True)]})
    palox_id = fields.Many2one(
        'fruit.palox', string='Palox', required=True, ondelete='restrict',
        states={'done': [('readonly', True)]})
    juice_destination = fields.Selection([
        ('withdrawal', 'Withdrawal'),
        ('sale', 'Sale'),
        ('mix', 'Mix'),
        ], string='Juice Destination', required=True,
        states={'done': [('readonly', True)]})
    mix_withdrawal_juice_qty = fields.Float(
        string='Requested Withdrawal Qty (L)',
        digits=dp.get_precision('Fruit Juice Volume'),
        states={'done': [('readonly', True)]},
        help="Quantity of fruit juice withdrawn by the farmer in liters")
    ripeness = fields.Selection([  # maturité
        ('green', 'Green'),
        ('in_between', 'In Between'),  # Tournantes
        ('optimal', 'Optimal'),
        ('overripen', 'Over Ripen'),  # surmatures
        ], string='Ripeness', required=True,
        states={'done': [('readonly', True)]})
    sanitary_state = fields.Selection([
        ('good', 'Good'),
        ('average', 'Average'),
        ('fair', 'Fair'),  # Passable
        ], string='Sanitary State', required=True,
        states={'done': [('readonly', True)]})
    juice_product_id = fields.Many2one(
        'product.product', string='Juice Type', required=True, index=True,
        domain=[('fruit_type', '=', 'juice')], ondelete='restrict',
        states={'done': [('readonly', True)]})
    product_fruit_culture_type = fields.Selection(
        related='juice_product_id.fruit_culture_type', readonly=True, store=True)
    production_id = fields.Many2one(
        'fruit.juice.production', string='Production', readonly=True)
    # START related fields for production
    production_date = fields.Date(
        related='production_id.date', string='Production Date', readonly=True,
        store=True)
    production_state = fields.Selection(
        related='production_id.state', string='Production State',
        readonly=True, store=True)
    compensation_type = fields.Selection(
        related='production_id.compensation_type', readonly=True, store=True)
    # END related fields for production
    juice_ratio = fields.Float(
        string='Juice Gross Ratio (% L)', digits=dp.get_precision('Fruit Juice Ratio'),
        readonly=True, group_operator='avg')
    juice_ratio_net = fields.Float(
        string='Juice Net Ratio (% L)', digits=dp.get_precision('Fruit Juice Ratio'),
        readonly=True, group_operator='avg')
    extra_ids = fields.One2many(
        'fruit.arrival.line.extra', 'line_id', string="Extra Items")
    extra_count = fields.Integer(
        compute='_compute_extra_count', string='Extra Item Lines', readonly=True)

    juice_qty_kg = fields.Float(
        string='Juice Qty (kg)',
        readonly=True, digits=dp.get_precision('Fruit Juice Volume'),
        help="Juice quantity in kg."
        "\nFirst-of-day compensation: not included."
        "\nLast-of-day compensation: already deducted."
        "\nShrinkage: not deducted."
        "\nFilter loss: not deducted.")
    juice_qty = fields.Float(
        string='Juice Qty (L)',
        readonly=True, digits=dp.get_precision('Fruit Juice Volume'),
        help="Juice quantity in liters."
        "\nFirst-of-day compensation: not included."
        "\nLast-of-day compensation: already deducted."
        "\nShrinkage: not deducted."
        "\nFilter loss: not deducted.")
    # We don't have the field 'compensation_last_fruit_qty'
    # because it would add un-needed complexity to have it on lines (it would also
    # required to have the compensation ratio on lines, etc...)
    # Instead, we use compensation_juice_qty (value set both for first and last)
    # The sign is always positive, even for last-of-day compensation
    compensation_juice_qty = fields.Float(
        string='Compensation Juice Qty (L)',
        readonly=True, digits=dp.get_precision('Fruit Juice Volume'),
        help="This field is used both for last of the day and first of "
        "the day compensations. The quantity is always positive, "
        "even for last-of-day compensations.")
    juice_qty_with_compensation = fields.Float(
        compute='_compute_juice_qty_with_compensation',
        string='Juice Qty with Compensation (L)', store=True,
        readonly=True, digits=dp.get_precision('Fruit Juice Volume'),
        help="Juice quantity with compensation in liters."
        "\nFirst-of-day compensation: included."
        "\nLast-of-day compensation: already deducted."
        "\nShrinkage: not deducted."
        "\nFilter loss: not deducted.")

    shrinkage_juice_qty = fields.Float(  # Sale and withdrawal
        string='Shrinkage Juice Qty (L)',
        readonly=True, digits=dp.get_precision('Fruit Juice Volume'))
    shrinkage_juice_qty_kg = fields.Float(  # Withdrawal only
        string='Shrinkage Juice Qty (kg)',
        readonly=True, digits=dp.get_precision('Fruit Weight'))

    withdrawal_juice_qty_kg = fields.Float(
        string='Withdrawal Juice Qty (kg)',
        readonly=True, digits=dp.get_precision('Fruit Weight'),
        help="Withdrawal juice quantity in kg."
        "\nFirst-of-day compensation: not included."
        "\nLast-of-day compensation: already deducted."
        "\nShrinkage: already deducted."
        "\nFilter loss: not applicable.")
    withdrawal_juice_qty = fields.Float(
        string='Withdrawal Juice Qty (L)',
        readonly=True, digits=dp.get_precision('Fruit Juice Volume'),
        help="Withdrawal juice quantity in liters."
        "\nFirst-of-day compensation: not included."
        "\nLast-of-day compensation: already deducted."
        "\nShrinkage: already deducted."
        "\nFilter loss: not applicable.")
    withdrawal_juice_qty_with_compensation = fields.Float(
        compute='_compute_withdrawal_juice_qty_with_compensation', store=True,
        string='Withdrawal Juice Qty with Compensation (L)',
        readonly=True, digits=dp.get_precision('Fruit Juice Volume'),
        help="Withdrawal juice quantity with compensation in liters (for statistics)."
        "\nFirst-of-day compensation: included."
        "\nLast-of-day compensation: already deducted."
        "\nShrinkage: already deducted."
        "\nFilter loss: not applicable.")

    to_sale_tank_juice_qty = fields.Float(
        string='Juice Qty to Sale Tank (L)',
        readonly=True, digits=dp.get_precision('Fruit Juice Volume'),
        help="Juice sent to sale tank in liters."
        "\nFirst-of-day compensation: not included."
        "\nLast-of-day compensation: already deducted."
        "\nShrinkage: not deducted (because we take shrinkage in sale tank)."
        "\nFilter loss: already deducted.")
    sale_juice_qty = fields.Float(
        string='Juice Qty Sold (L)',
        readonly=True, digits=dp.get_precision('Fruit Juice Volume'),
        help="Juice quantity sold in liters."
        "\nFirst-of-day compensation: included."
        "\nLast-of-day compensation: already deducted."
        "\nShrinkage: already deducted."
        "\nFilter loss: already deducted.")
    juice_qty_net = fields.Float(
        string='Net Juice Qty (L)',
        readonly=True, digits=dp.get_precision('Fruit Juice Volume'),
        help="Net juice quantity produced in liters."
        "\nFirst-of-day compensation: included."
        "\nLast-of-day compensation: already deducted."
        "\nShrinkage: already deducted."
        "\nFilter loss: already deducted.")

    filter_loss_juice_qty = fields.Float(
        string='Juice Qty Lost in Filter (L)',
        readonly=True, digits=dp.get_precision('Fruit Juice Volume'))
    withdrawal_move_id = fields.Many2one(
        'stock.move', string='Withdrawal Move', readonly=True)
    out_invoice_id = fields.Many2one(
        'account.invoice', string="Customer Invoice", readonly=True)
    in_invoice_line_id = fields.Many2one(
        'account.invoice.line', string='Vendor Bill Line', readonly=True)
    company_currency_id = fields.Many2one(
        related='arrival_id.company_id.currency_id', store=True, readonly=True)
    juice_sale_price_unit = fields.Monetary(
        string='Juice Sale Unit Price',
        readonly=True, currency_field='company_currency_id',
        help="Juice sale price per liter without taxes in company currency.")
    juice_service_sale_price_unit = fields.Monetary(
        string='Juice Service Unit Price (Sale Only)',
        readonly=True, currency_field='company_currency_id',
        help='TODO')
    juice_sale_price_total = fields.Monetary(
        string='Juice Sale Price Total',
        readonly=True, store=True, currency_field='company_currency_id')
    juice_service_sale_price_total = fields.Monetary(
        string='Juice Service Price Total (Sale Only)',
        readonly=True, store=True, currency_field='company_currency_id')

    _sql_constraints = [(
        'fruit_qty_positive',
        'CHECK(fruit_qty >= 0)',
        'The fruit quantity must be positive or null.'), (
        'mix_withdrawal_juice_qty_qty_positive',
        'CHECK(mix_withdrawal_juice_qty >= 0)',
        'The requested withdrawal qty must be positive or null.'),
        ]

    @api.depends('extra_ids')
    def _compute_extra_count(self):
        res = self.env['fruit.arrival.line.extra'].read_group(
            [('line_id', 'in', self.ids)], ['line_id'], ['line_id'])
        for re in res:
            self.browse(re['line_id'][0]).extra_count = re['line_id_count']

    @api.depends('juice_qty', 'compensation_type', 'compensation_juice_qty')
    def _compute_juice_qty_with_compensation(self):
        for line in self:
            juice_qty_with_compensation = line.juice_qty
            if line.compensation_type == 'first':
                juice_qty_with_compensation += line.compensation_juice_qty
            line.juice_qty_with_compensation = juice_qty_with_compensation

    @api.depends('withdrawal_juice_qty', 'compensation_type', 'compensation_juice_qty', 'juice_destination')
    def _compute_withdrawal_juice_qty_with_compensation(self):
        for line in self:
            withdrawal_juice_qty_w_comp = line.withdrawal_juice_qty
            if line.compensation_type == 'first' and line.juice_destination == 'withdrawal':
                withdrawal_juice_qty_w_comp += line.compensation_juice_qty
            line.withdrawal_juice_qty_with_compensation = withdrawal_juice_qty_w_comp

    @api.depends('sale_juice_qty', 'juice_service_sale_price_unit', 'juice_sale_price_unit')
    def _compute_juice_price_total(self):
        for line in self:
            qty = line.sale_juice_qty
            line.juice_sale_price_total = line.juice_sale_price_unit * qty
            line.juice_service_sale_price_total = line.juice_service_sale_price_unit * qty

    @api.onchange('juice_destination')
    def juice_destination_change(self):
        if self.juice_destination != 'mix':
            self.mix_withdrawal_juice_qty = 0

    @api.onchange('palox_weight')
    def palox_weight_change(self):
        prec = self.env['decimal.precision'].precision_get('Fruit Weight')
        res = {
            'warning': {
                'title': _('Error'),
                'message': '',
                },
            }
        if not float_is_zero(self.palox_weight, precision_digits=prec):
            if not self.palox_id:
                self.palox_weight = 0
                res['warning']['message'] = _('Select the palox before entering the gross palox weight. The gross palox weight has been reset to 0 kg.')
                return res
            else:
                if float_is_zero(self.palox_id.empty_weight, precision_digits=prec):
                    self.palox_weight = 0
                    res['warning']['message'] = _("Missing empty weight on palox '%s'. The gross palox weight has been reset to 0 kg.") % self.palox_id.name
                    return res
                fruit_qty = self.palox_weight - self.palox_id.empty_weight - self.palox_id.weight
                if float_compare(fruit_qty, 0, precision_digits=prec) <= 0:
                    self.palox_weight = 0
                    res['warning']['message'] = _("Wrong gross palox weight: the fruit qty would be negative (%s kg). The gross palox weight has been reset to 0 kg.") % fruit_qty
                    return res
                self.fruit_qty = fruit_qty

    @api.onchange('palox_id')
    def palox_id_change(self):
        prec = self.env['decimal.precision'].precision_get('Fruit Weight')
        if not float_is_zero(self.palox_weight, precision_digits=prec):
            self.palox_weight = 0
            self.fruit_qty = 0
            res = {
                'warning': {
                    'title': _('Error'),
                    'message': _("You changed the palox and the fruit qty was set via the palox gross weight, so you must re-enter the palox gross weight."),
                    }
                }
            return res

    def unlink(self):
        pr_oli = self.env['decimal.precision'].precision_get('Fruit Weight')
        for line in self:
            if line.production_id:
                raise UserError(_(
                    "Deletion of arrival line %s not allowed because "
                    "it is linked to juice production %s.") % (
                        line.name, line.production_id.name))
            if not float_is_zero(line.fruit_qty, precision_digits=pr_oli):
                raise UserError(_(
                    "Deletion of arrival line %s not allowed because "
                    "the fruit qty (%s kg) is not null.") % (line.name, line.fruit_qty))
            if line.state == 'done':
                raise UserError(_(
                    "Deletion of arrival line %s not allowed because "
                    "it is in done state.") % line.name)
        return super(FruitArrivalLine, self).unlink()

    @api.depends('name', 'commercial_partner_id', 'variant_id')
    def name_get(self):
        res = []
        for rec in self:
            name = rec.name
            if rec.commercial_partner_id:
                name = '%s (%s, %s)' % (name, rec.commercial_partner_id.name, rec.variant_id.name)
            res.append((rec.id, name))
        return res

    def juice_qty_compute_other_vals(self, juice_qty, compensation_juice_qty, ratio):
        pr_juice = self.env['decimal.precision'].precision_get(
            'Fruit Juice Volume')
        pr_oli = self.env['decimal.precision'].precision_get('Fruit Weight')
        pr_ratio = self.env['decimal.precision'].precision_get(
            'Fruit Juice Ratio')
        company = self.production_id.company_id
        density = company.fruit_juice_density
        shrinkage_ratio = company.fruit_shrinkage_ratio
        filter_ratio = company.fruit_filter_ratio
        juice_destination = self.juice_destination
        ctype = self.compensation_type
        if not density:
            raise UserError(_(
                "Missing Fruit Juice Density on company '%s'")
                % company.display_name)
        juice_qty = float_round(juice_qty, precision_digits=pr_juice)
        compensation_juice_qty = float_round(
            compensation_juice_qty, precision_digits=pr_juice)
        juice_qty_kg = float_round(
            juice_qty * density, precision_digits=pr_oli)
        withdrawal_juice_qty = withdrawal_juice_qty_kg = filter_loss_juice_qty = 0.0
        sale_juice_qty = to_sale_tank_juice_qty = ratio_net = 0.0
        shrinkage_juice_qty = float_round(
            juice_qty * shrinkage_ratio / 100, precision_digits=pr_juice)
        shrinkage_juice_qty_kg = float_round(
            shrinkage_juice_qty * density, precision_digits=pr_oli)
        juice_minus_shrinkage = juice_qty - shrinkage_juice_qty

        if juice_destination == 'withdrawal':
            withdrawal_juice_qty = float_round(
                juice_minus_shrinkage, precision_digits=pr_juice)
            withdrawal_juice_qty_kg = float_round(
                juice_qty_kg - shrinkage_juice_qty_kg, precision_digits=pr_oli)

        elif juice_destination == 'sale':
            filter_loss_juice_qty = juice_qty * filter_ratio / 100
            sale_juice_qty = juice_minus_shrinkage - filter_loss_juice_qty
            if ctype == 'first':
                sale_juice_qty += compensation_juice_qty
            to_sale_tank_juice_qty = juice_qty - filter_loss_juice_qty

        elif juice_destination == 'mix':
            # When juice_destination == 'mix' and ctype == 'first',
            # the compensation is always for SALE
            # (compensation is withdrawn only when the requested qty is
            # superior to juice production minus shrinkage without compensation
            if float_compare(
                    juice_minus_shrinkage, self.mix_withdrawal_juice_qty,
                    precision_digits=pr_juice) >= 0:
                withdrawal_juice_qty = self.mix_withdrawal_juice_qty
                juice_qty_minus_withdrawal = juice_qty - withdrawal_juice_qty
                filter_loss_juice_qty = \
                    juice_qty_minus_withdrawal * filter_ratio / 100
                sale_juice_qty = juice_qty_minus_withdrawal \
                    - shrinkage_juice_qty - filter_loss_juice_qty
                to_sale_tank_juice_qty = juice_qty_minus_withdrawal \
                    - filter_loss_juice_qty
                if ctype == 'first':
                    sale_juice_qty += compensation_juice_qty
            else:
                withdrawal_juice_qty = juice_minus_shrinkage
                # rewrite juice destination, for shrinkage stock move
                juice_destination = 'withdrawal'
                # Nothing more to do for ctype == 'first':
            withdrawal_juice_qty_kg = withdrawal_juice_qty * density
        # Compute net ratio, with compensations
        juice_qty_net = juice_minus_shrinkage - filter_loss_juice_qty
        if ctype == 'first':
            juice_qty_net += compensation_juice_qty
        ratio_net = float_round(
            100 * juice_qty_net / self.fruit_qty,
            precision_digits=pr_ratio)

        vals = {
            'juice_qty_kg': juice_qty_kg,
            'juice_qty': juice_qty,
            'juice_ratio': ratio,
            'juice_ratio_net': ratio_net,
            'shrinkage_juice_qty': shrinkage_juice_qty,
            'shrinkage_juice_qty_kg': shrinkage_juice_qty_kg,
            'withdrawal_juice_qty_kg': withdrawal_juice_qty_kg,
            'withdrawal_juice_qty': withdrawal_juice_qty,
            'juice_destination': juice_destination,
            'filter_loss_juice_qty': filter_loss_juice_qty,
            'sale_juice_qty': sale_juice_qty,
            'to_sale_tank_juice_qty': to_sale_tank_juice_qty,
            'compensation_juice_qty': compensation_juice_qty,
            'juice_qty_net': juice_qty_net,
            }
        return vals

    def pre_prepare_invoice_line(self, product, invoice):
        ailo = self.env['account.invoice.line']
        il_vals = {
            'product_id': product.id,
            'invoice_id': invoice.id,
            }
        il_vals = ailo.play_onchanges(il_vals, ['product_id'])
        if not il_vals.get('account_id'):
            raise UserError(_(
                "Missing account on product '%s' or on it's related product category.")
                % product.display_name)
        return il_vals

    def prepare_invoice(self, invoice_type, invoice_reference=False):
        # pr_tax = self.env['decimal.precision'].precision_get(
        #    'Fruit Juice Tax Price Unit')
        # pr_pri = self.env['decimal.precision'].precision_get(
        #    'Product Price')
        aio = self.env['account.invoice']
        partner = self[0].commercial_partner_id
        company = self.env.user.company_id
        origin = [line.name for line in self]
        if len(origin) > 3:
            origin = origin[:3] + ['...']
        origin = ', '.join(origin)
        currency = partner.property_product_pricelist.currency_id
        vals = {
            'partner_id': partner.id,
            'currency_id': currency.id,
            'type': invoice_type,
            'company_id': company.id,
            'origin': origin,
            'reference': invoice_reference,
        }
        vals = aio.play_onchanges(vals, ['partner_id'])
        return vals

    def create_in_invoice_lines(self, invoice):
        ailo = self.env['account.invoice.line'].with_context(type='in_invoice')
        pr_oli = self.env['decimal.precision'].precision_get('Fruit Weight')
        partner = invoice.partner_id
        lang = partner.lang or self.env.user.lang
        pricelist = partner.property_product_pricelist
        currency = pricelist.currency_id
        saledict = {}  # key = arrival, value = {'product': sale_juice_qty}
        # I can't do a double groupby via read_group()
        if partner.fruit_sale_pricelist_id:
            product2price = partner.fruit_sale_pricelist_id.prepare_speeddict()
        else:
            product2price = {}
        for line in self:
            arrival = line.arrival_id
            product = line.juice_product_id
            if float_compare(
                    line.sale_juice_qty, 0, precision_digits=pr_oli) > 0:
                if line.arrival_id in saledict:
                    if product in saledict[arrival]:
                        saledict[arrival][product] += line.sale_juice_qty
                    else:
                        saledict[arrival][product] = line.sale_juice_qty
                else:
                    saledict[arrival] = {product: line.sale_juice_qty}
        total_juice_qty = 0.0
        for arrival, pdict in list(saledict.items()):
            for product, quantity in list(pdict.items()):
                total_juice_qty += quantity
                # TODO: move to prepare line method
                il_vals = self.pre_prepare_invoice_line(product, invoice)
                il_vals['origin'] = arrival.name
                # TODO: translate in right language
                arrival_date_formatted = format_date(
                    fields.Date.from_string(arrival.date),
                    format='short', locale=lang or 'en_US')
                il_vals['name'] = _('%s (Arrival %s dated %s)') % (
                    product.with_context(lang=lang).name,
                    arrival.name, arrival_date_formatted)
                il_vals['quantity'] = quantity
                seller = product._select_seller(
                    partner, quantity=quantity, uom_id=product.uom_id)
                if seller:
                    price_unit = seller.currency_id.compute(
                        seller.price, currency)
                elif product in product2price:
                    price_unit = product2price[product]
                else:
                    price_unit = 0.0
                il_vals['price_unit'] = price_unit
                iline = ailo.create(il_vals)
                arrival.line_ids.write({
                    'in_invoice_line_id': iline.id})
        # TODO translate in right language
        invoice.comment = _(
            "Total juice quantity: %s L") % formatLang(
                self.env, total_juice_qty, dp='Fruit Juice Volume')
        invoice.compute_taxes()

    def create_out_invoice_lines(self, invoice):
        ailo = self.env['account.invoice.line'].with_context(type='out_invoice')
        ppo = self.env['product.product']
        pr_juice = self.env['decimal.precision'].precision_get(
            'Fruit Juice Volume')
        pr_oli = self.env['decimal.precision'].precision_get('Fruit Weight')
        company = invoice.company_id
        partner = invoice.partner_id
        pricelist = partner.property_product_pricelist
        season = self[0].season_id
        totals = self.read_group(
            [('id', 'in', self.ids)],
            ['fruit_qty', 'juice_qty', 'juice_qty_with_compensation',
             'shrinkage_juice_qty', 'filter_loss_juice_qty'], [])[0]
        if float_compare(
                totals['juice_qty'], 0, precision_digits=pr_juice) <= 0:
            return False
        if not company.fruit_juice_production_product_id:
            raise UserError(_(
                "Missing production product on company %s.")
                % company.name)
        if not company.fruit_juice_leaf_removal_product_id:
            raise UserError(_(
                "Missing leaf removal product on company %s.")
                % company.name)
        if not company.fruit_juice_tax_product_id:
            raise UserError(_(
                "Missing tax product on company %s.") % company.name)
        if season.early_bird_date and not company.fruit_juice_early_bird_discount_product_id:
            raise UserError(_(
                "Missing early bird discount product on company %s.")
                % company.name)
        # Production
        il_vals = self.pre_prepare_invoice_line(
            company.fruit_juice_production_product_id, invoice)
        il_vals['quantity'] = totals['fruit_qty']
        il_vals['price_unit'] = pricelist.get_product_price(
            company.fruit_juice_production_product_id,
            totals['fruit_qty'], partner)
        ailo.create(il_vals)
        # additionnal service options are only invoiced on withdrawal
        # cf ('juice_destination', '=', 'withdrawal') in domain
        product_totals = self.read_group(
            [('id', 'in', self.ids), ('juice_destination', '=', 'withdrawal')],
            ['fruit_qty', 'juice_product_id'], ['juice_product_id'])
        for product_total in product_totals:
            product = ppo.browse(product_total['juice_product_id'][0])
            for srv_product in product.fruit_invoice_service_ids:
                il_vals = self.pre_prepare_invoice_line(srv_product, invoice)
                il_vals['quantity'] = product_total['fruit_qty']
                il_vals['price_unit'] = pricelist.get_product_price(
                    srv_product, product_total['fruit_qty'], partner)
                ailo.create(il_vals)
        # Discount
        if season.early_bird_date:
            total_disc = self.read_group(
                [('id', 'in', self.ids),
                 ('arrival_date', '<=', season.early_bird_date)],
                ['fruit_qty'], [])
            if total_disc and total_disc[0]['fruit_qty'] and float_compare(
                    total_disc[0]['fruit_qty'], 0,
                    precision_digits=pr_oli) > 0:
                il_vals = self.pre_prepare_invoice_line(
                    company.fruit_juice_early_bird_discount_product_id, invoice)
                # with Factur-X, we can't have negative prices
                # so I put a negative qty
                qty = total_disc[0]['fruit_qty']
                il_vals['quantity'] = qty * -1
                il_vals['price_unit'] = pricelist.get_product_price(
                    company.fruit_juice_early_bird_discount_product_id,
                    qty, partner)
                ailo.create(il_vals)
        # leaf removal
        total_leaf = self.read_group(
            [('id', 'in', self.ids), ('leaf_removal', '=', True)],
            ['fruit_qty'], [])
        if (
                total_leaf and total_leaf[0]['fruit_qty'] and
                float_compare(
                    total_leaf[0]['fruit_qty'], 0,
                    precision_digits=pr_oli) > 0):
            il_vals = self.pre_prepare_invoice_line(
                company.fruit_juice_leaf_removal_product_id, invoice)
            qty = total_leaf[0]['fruit_qty']
            il_vals['quantity'] = qty
            il_vals['price_unit'] = pricelist.get_product_price(
                company.fruit_juice_leaf_removal_product_id,
                qty, partner)
            ailo.create(il_vals)
        # AFIDOL Tax
        tax_product = company.fruit_juice_tax_product_id
        if tax_product.uom_id != self.env.ref('uom.product_uom_kgm'):
            raise UserError(_(
                "The unit of measure of the juice tax product (%s) should be in kg.")
                % tax_product.display_name)
        il_vals = self.pre_prepare_invoice_line(tax_product, invoice)
        qty = totals['juice_qty_with_compensation'] - totals['shrinkage_juice_qty']\
            - totals['filter_loss_juice_qty']
        price_unit_kg = pricelist.get_product_price(
            tax_product, qty, partner)
        qty_kg = float_round(
            qty * company.fruit_juice_density, precision_digits=pr_juice)
        il_vals['quantity'] = qty_kg
        il_vals['price_unit'] = price_unit_kg
        il_vals['name'] += _(" (%s L = %s kg)") % (
            formatLang(self.env, qty, dp='Fruit Juice Volume'),
            formatLang(self.env, qty_kg, dp='Fruit Juice Volume'))
        ailo.create(il_vals)
        # Extra items
        extra_totals = self.env['fruit.arrival.line.extra'].read_group(
            [
                ('line_id', 'in', self.ids),
                '|', ('fillup', '=', False),
                     ('fruit_bottle_free_full', '=', False)],
            ['product_id', 'qty'], ['product_id'])
        for extra_total in extra_totals:
            product_id = extra_total['product_id'][0]
            product = ppo.browse(product_id)
            qty = extra_total['qty']
            il_vals = self.pre_prepare_invoice_line(product, invoice)
            il_vals['quantity'] = qty
            il_vals['price_unit'] = pricelist.get_product_price(
                product, qty, partner)
            ailo.create(il_vals)
        invoice.compute_taxes()

    def in_invoice_create(self):
        aio = self.env['account.invoice']
        vals = self.prepare_invoice('in_invoice')
        invoice = aio.with_context(type='in_invoice').create(vals)
        self.create_in_invoice_lines(invoice)
        return invoice

    def out_invoice_create(self):
        aio = self.env['account.invoice']
        vals = self.prepare_invoice('out_invoice')
        invoice = aio.with_context(type='out_invoice').create(vals)
        self.create_out_invoice_lines(invoice)
        self.write({'out_invoice_id': invoice.id})
        return invoice

    def check_arrival_line_hook(self, i, warn_msgs):
        return

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(FruitArrivalLine, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        return self.env.user.company_id.current_season_update(res, view_type)


class FruitArrivalLineExtra(models.Model):
    _name = 'fruit.arrival.line.extra'
    _description = 'Extra items linked to the arrival line'

    line_id = fields.Many2one(
        'fruit.arrival.line', string='Arrival Line', ondelete='cascade')
    product_id = fields.Many2one(
        'product.product', string='Extra Product',
        required=True, ondelete='restrict',
        domain=[
            ('fruit_type', 'in', ('bottle', 'analysis', 'extra_service')),
            '|', ('tracking', '=', False), ('tracking', '=', 'none')])
    product_fruit_type = fields.Selection(
        related='product_id.fruit_type', readonly=True, store=True)
    qty = fields.Float(
        string='Quantity', default=1,
        digits=dp.get_precision('Product Unit of Measure'), required=True)
    uom_id = fields.Many2one(
        related='product_id.uom_id', readonly=True)
    fillup = fields.Boolean(string='Fill-up')
    fruit_bottle_free_full = fields.Boolean(
        related='product_id.fruit_bottle_free_full', store=True, readonly=True)

    @api.onchange('product_id')
    def product_id_change(self):
        if (
                self.product_id and
                self.product_id.fruit_type == 'bottle' and
                self._context.get('fruit_fillup_bottles')):
            self.fillup = True
        else:
            self.fillup = False

    @api.constrains('product_id', 'fillup')
    def line_extra_check(self):
        for extra in self:
            if extra.fillup and extra.product_id.fruit_type != 'bottle':
                raise ValidationError(_(
                    "You cannot enable the fill-up option on product '%s' "
                    "which is not an juice bottle.")
                    % extra.product_id.display_name)
