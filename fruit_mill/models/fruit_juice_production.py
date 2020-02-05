# Copyright 2018 Barroux Abbey (https://www.barroux.org/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
import odoo.addons.decimal_precision as dp
from odoo.tools import float_compare, float_round


class FruitJuiceProduction(models.Model):
    _name = 'fruit.juice.production'
    _description = 'Fruit Juice Production'
    _order = 'date desc, sequence, id desc'
    _inherit = ['mail.thread']

    name = fields.Char(string='Production Number', required=True, default='/')
    company_id = fields.Many2one(
        'res.company', string='Company', ondelete='cascade', required=True,
        states={'done': [('readonly', True)]},
        default=lambda self: self.env['res.company']._company_default_get())
    season_id = fields.Many2one(
        'fruit.season', string='Season', required=True, index=True,
        default=lambda self: self.env.user.company_id.current_season_id.id,
        states={'done': [('readonly', True)]})
    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Warehouse', required=True, index=True,
        domain=[('fruit_mill', '=', True)],
        default=lambda self: self.env.user._default_fruit_mill_wh(),
        track_visibility='onchange')
    palox_id = fields.Many2one(
        'fruit.palox', string='Palox', required=True, readonly=True,
        ondelete='restrict',
        states={'draft': [('readonly', False)]}, track_visibility='onchange')
    # STOCK LOCATIONS
    sale_location_id = fields.Many2one(
        'stock.location', string='Sale Tank',
        states={'done': [('readonly', True)]},
        track_visibility='onchange')
    # not a pb to have withdrawal_location_id required because
    # this field has a default value
    withdrawal_location_id = fields.Many2one(
        'stock.location', string='Withdrawal Location', required=True,
        states={'done': [('readonly', True)]},
        domain=[('fruit_tank_type', '=', False), ('usage', '=', 'internal')])
    shrinkage_location_id = fields.Many2one(
        'stock.location', string='Shrinkage Tank',
        states={'done': [('readonly', True)]},
        track_visibility='onchange')
    compensation_location_id = fields.Many2one(
        'stock.location', string='Compensation Tank', readonly=True,
        states={'draft': [('readonly', False)]},  # so that the onchange works
        track_visibility='onchange')
    compensation_sale_location_id = fields.Many2one(
        'stock.location', string='Compensation Sale Tank',
        states={'done': [('readonly', True)]}, track_visibility='onchange')
    compensation_juice_product_id = fields.Many2one(
        'product.product', string='Compensation Juice Type', readonly=True)
    compensation_type = fields.Selection([
        ('none', 'No Compensation'),
        ('first', 'First of the Day'),
        ('last', 'Last of the Day'),
        ], string='Compensation Type', default='none', readonly=True,
        track_visibility='onchange')
    compensation_last_fruit_qty = fields.Float(
        string='Fruit Compensation Qty',
        digits=dp.get_precision('Fruit Weight'), readonly=True,
        track_visibility='onchange', help="Fruit compensation in kg")
    compensation_ratio = fields.Float(
        string='Compensation Ratio', digits=dp.get_precision('Fruit Juice Ratio'),
        readonly=True, track_visibility='onchange')
    fruit_qty = fields.Float(
        string='Fruit Qty', compute='_compute_lines',
        digits=dp.get_precision('Fruit Weight'), readonly=True, store=True,
        track_visibility='onchange',
        help='Fruit quantity without compensation in kg')
    to_sale_tank_juice_qty = fields.Float(
        string='Juice Qty to Sale Tank (L)', compute='_compute_lines',
        digits=dp.get_precision('Fruit Juice Volume'), readonly=True, store=True)
    to_compensation_sale_tank_juice_qty = fields.Float(
        string='Juice Qty to Compensation Sale Tank (L)', compute='_compute_lines',
        digits=dp.get_precision('Fruit Juice Volume'), readonly=True, store=True)
    compensation_juice_qty = fields.Float(
        string='Juice Compensation (L)',
        digits=dp.get_precision('Fruit Juice Volume'), readonly=True,
        track_visibility='onchange')
    compensation_juice_qty_kg = fields.Float(
        string='Juice Compensation (kg)',
        digits=dp.get_precision('Fruit Weight'), readonly=True)
    juice_destination = fields.Selection([
        ('withdrawal', 'Withdrawal'),
        ('sale', 'Sale'),
        ('mix', 'Mix'),
        ], string='Juice Destination', compute='_compute_juice_destination',
        readonly=True)
    juice_product_id = fields.Many2one(
        'product.product', string='Juice Type', readonly=True,
        track_visibility='onchange')
    fruit_culture_type = fields.Selection(
        related='juice_product_id.fruit_culture_type', readonly=True, store=True)
    fruit_culture_type_logo = fields.Binary(
        compute='_compute_fruit_culture_type_logo',
        string='Fruit Culture Type Logo', readonly=True)
    juice_qty_kg = fields.Float(
        string='Juice Quantity (kg)', digits=dp.get_precision('Fruit Weight'),
        readonly=True, track_visibility='onchange')  # written by ratio2force wizard
    juice_qty = fields.Float(
        string='Juice Quantity (L)', digits=dp.get_precision('Fruit Juice Volume'),
        readonly=True, track_visibility='onchange')  # written by ratio2force wizard
    ratio = fields.Float(
        string='Gross Ratio (% L)', digits=dp.get_precision('Fruit Juice Ratio'),
        readonly=True, group_operator='avg',
        help="This ratio gives the number of liters of fruit juice for "
        "100 kg of fruits.")  # Yes, it's a ratio between liters and kg !!!
    date = fields.Date(
        string='Date', default=fields.Date.context_today, required=True,
        states={'done': [('readonly', True)]}, track_visibility='onchange')
    day_position = fields.Integer(
        compute='_compute_day_position', readonly=True, string='Order')
    sample = fields.Boolean(
        string='Sample', readonly=True,
        states={'draft': [('readonly', False)], 'ratio': [('readonly', False)]})
    farmers = fields.Char(string='Farmers', readonly=True)
    decanter_speed = fields.Integer(
        string='Decanter Speed', states={'done': [('readonly', True)]})
    sequence = fields.Integer(default=10)
    state = fields.Selection([
        ('draft', 'Palox Selection'),
        ('ratio', 'Enter Production Result'),
        ('force', 'Force Ratio'),
        ('pack', 'Package'),
        ('check', 'Final Check'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ], string='State', default='draft', readonly=True,
        track_visibility='onchange')
    done_datetime = fields.Datetime(
        string='Date Done', readonly=True, copy=False)
    shrinkage_move_id = fields.Many2one(
        'stock.move', string='Shrinkage Stock Move', readonly=True, copy=False)
    sale_move_id = fields.Many2one(
        'stock.move', string='Sale Move', readonly=True)
    compensation_last_move_id = fields.Many2one(
        'stock.move', string='Compensation Last of the Day Move', readonly=True)
    line_ids = fields.One2many(
        'fruit.arrival.line', 'production_id', string='Arrival Lines',
        readonly=True)

    _sql_constraints = [
        ('juice_qty_kg_positive', 'CHECK(juice_qty_kg >= 0)', 'The juice quantity must be positive.'),
        ('compensation_last_fruit_qty_positive', 'CHECK(compensation_last_fruit_qty >= 0)', 'The compensation fruit quantity must be positive.'),
        ('compensation_juice_qty_positive', 'CHECK(compensation_juice_qty >= 0)', 'The compensation juice quantity must be positive.'),
        ]

    @api.constrains('compensation_ratio', 'compensation_type')
    def check_production(self):
        for prod in self:
            min_ratio, max_ratio = prod.company_id.fruit_min_max_ratio()
            if prod.compensation_type == 'last':
                cratio = prod.compensation_ratio
                if cratio < min_ratio or cratio > max_ratio:
                    raise ValidationError(_(
                        "The compensation ratio (%s %%) is not realistic.")
                        % cratio)

    @api.onchange('warehouse_id')
    def warehouse_change(self):
        if self.warehouse_id:
            wh = self.warehouse_id
            if wh.fruit_withdrawal_loc_id:
                self.withdrawal_location_id = wh.fruit_withdrawal_loc_id
            if wh.fruit_compensation_loc_id:
                self.compensation_location_id = wh.fruit_compensation_loc_id

    @api.onchange('palox_id')
    def palox_change(self):
        if self.palox_id:
            self.juice_product_id = self.palox_id.juice_product_id
        else:
            self.juice_product_id = False

    @api.depends(
        'line_ids.fruit_qty', 'line_ids.to_sale_tank_juice_qty',
        'line_ids.juice_destination', 'line_ids.compensation_juice_qty')
    def _compute_lines(self):
        res = self.env['fruit.arrival.line'].read_group(
            [('production_id', 'in', self.ids)],
            ['production_id', 'fruit_qty', 'to_sale_tank_juice_qty'],
            ['production_id'])
        for re in res:
            production = self.browse(re['production_id'][0])
            production.fruit_qty = re['fruit_qty']
            production.to_sale_tank_juice_qty = re['to_sale_tank_juice_qty']
        cres = self.env['fruit.arrival.line'].read_group(
            [('production_id', 'in', self.ids),
             ('juice_destination', 'in', ('sale', 'mix'))],
            ['production_id', 'compensation_juice_qty'],
            ['production_id'])
        for cre in cres:
            production = self.browse(cre['production_id'][0])
            production.to_compensation_sale_tank_juice_qty = cre['compensation_juice_qty']

    @api.depends('line_ids.juice_destination')
    def _compute_juice_destination(self):
        for prod in self:
            juice_destination = False
            if prod.line_ids:
                dests = [line.juice_destination for line in prod.line_ids]
                if all([dest == 'sale' for dest in dests]):
                    juice_destination = 'sale'
                elif all([dest == 'withdrawal' for dest in dests]):
                    juice_destination = 'withdrawal'
                else:
                    juice_destination = 'mix'
            prod.juice_destination = juice_destination

    @api.depends('juice_product_id.fruit_culture_type')
    def _compute_fruit_culture_type_logo(self):
        type2filename = {
            'organic': 'organic_logo_done.png',
            'conversion': 'organic_logo_conversion_done.png',
        }
        for prod in self:
            logo = False
            if prod.fruit_culture_type in type2filename:
                filename = type2filename[prod.fruit_culture_type]
                fname_path = 'fruit_mill/static/image/%s' % filename
                f = tools.file_open(fname_path, 'rb')
                f_binary = f.read()
                if f_binary:
                    logo = f_binary.encode('base64')
            prod.fruit_culture_type_logo = logo

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'fruit.juice.production')
        return super(FruitJuiceProduction, self).create(vals)

    def cancel(self):
        for production in self:
            if production.state == 'done':
                raise UserError(_(
                    "Cannot cancel production %s which is in 'done' state.")
                    % production.name)
        self.write({
            'state': 'cancel',
            'juice_qty': 0,
            'juice_qty_kg': 0,
            'ratio': 0,
            'to_sale_tank_juice_qty': 0,
            'to_compensation_sale_tank_juice_qty': 0,
            })

    def back2draft(self):
        self.ensure_one()
        assert self.state == 'cancel'
        self.write({'state': 'draft'})

    def draft2ratio(self):
        """Attach arrival lines to fruit.juice.production"""
        self.ensure_one()
        assert self.state == 'draft'
        oalo = self.env['fruit.arrival.line']
        pr_oli = self.env['decimal.precision'].precision_get('Fruit Weight')
        if not self.line_ids:
            draft_lines = oalo.search([
                ('palox_id', '=', self.palox_id.id),
                ('warehouse_id', '=', self.warehouse_id.id),
                ('state', '=', 'draft'),
                ('production_id', '=', False)])
            if draft_lines:
                raise UserError(_(
                    "Arrival line %s is linked to palox %s but it is still "
                    "in draft state. If you want to take this arrival line "
                    "in this production, you should validate the arrival. "
                    "Otherwise, you should cancel the arrival.")
                    % (draft_lines[0].name, self.palox_id.name))
            done_lines = oalo.search([
                ('palox_id', '=', self.palox_id.id),
                ('warehouse_id', '=', self.warehouse_id.id),
                ('state', '=', 'done'),
                ('production_id', '=', False)])
            if not done_lines:
                raise UserError(_(
                    "The palox %s is empty or currently in production.")
                    % self.palox_id.name)
            done_lines.write({'production_id': self.id})
            # Free the palox
            self.palox_id.juice_product_id = False
        juice_dests = []
        juice_product = False
        sample = False
        farmers = []
        for l in self.line_ids:
            juice_dests.append(l.juice_destination)
            if juice_product:
                if juice_product != l.juice_product_id:
                    raise UserError(_(
                        "The juice type of arrival line %s is %s, "
                        "but it is %s on the first arrival line "
                        "of palox %s.") % (
                            l.name,
                            l.juice_product_id.name,
                            juice_product.name,
                            self.palox_id.name))
            else:
                juice_product = l.juice_product_id
            if l.season_id != self.season_id:
                raise UserError(_(
                    "The season of arrival line %s is '%s', but the juice "
                    "production %s is attached to season '%s'.") % (
                        l.name, l.season_id.name, self.name, self.season_id.name))
            farmers.append(l.commercial_partner_id.name)
            if float_compare(l.fruit_qty, 0, precision_digits=pr_oli) <= 0:
                raise UserError(_(
                    "On line %s, the fruit quantity is null.") % l.name)
            if not sample:
                for extra in l.extra_ids:
                    if extra.product_fruit_type == 'analysis':
                        sample = True
                        break
        sloc = self.warehouse_id.fruit_get_shrinkage_tank(juice_product)

        self.write({
            'farmers': ' / '.join(farmers),
            'sample': sample,
            'state': 'ratio',
            'juice_product_id': juice_product.id,
            'shrinkage_location_id': sloc and sloc.id or False
            })

    def start_ratio2force(self):
        self.ensure_one()
        assert self.state == 'ratio'
        cloc = self.compensation_location_id
        # We cannot do that in the wizard fruit.juice.production.compensation
        # because, at the time of the wizard, the previous last of day
        # compensation may not be done yet, so the compensation tank
        # may be empty
        if self.compensation_type == 'last':
            # cloc.juice_product_id will be written a second time in
            # check2done (in case the wizard swap product is used)
            cloc.sudo().juice_product_id = self.juice_product_id.id
        compensation_juice_qty = self.compensation_check_tank()
        if self.compensation_type == 'first':
            density = self.company_id.fruit_juice_density
            self.write({
                'compensation_juice_qty': compensation_juice_qty,
                'compensation_juice_qty_kg': compensation_juice_qty * density,
                'compensation_juice_product_id': cloc.juice_product_id.id,
                })
        action = self.env['ir.actions.act_window'].for_xml_id(
            'fruit_mill', 'fruit_juice_production_ratio2force_action')
        action['context'] = {
            'default_production_id': self.id,
            'default_compensation_sale_location_id': self.compensation_sale_location_id.id or False,
            'default_sale_location_id': self.sale_location_id.id or False,
            }
        return action

    def ratio2force(self):
        self.ensure_one()
        assert self.state == 'ratio'
        new_state = 'force'
        if len(self.line_ids) == 1:  # Skip force ratio step
            new_state = 'pack'
            if self.juice_destination == 'sale':  # Skip pack
                new_state = 'check'
        self.write({
            'state': new_state,
            })
        self.set_qty_on_lines()

    def force2pack(self):
        self.ensure_one()
        assert self.state == 'force'
        new_state = 'pack'
        if self.juice_destination == 'sale':  # Skip pack
            new_state = 'check'
        self.write({'state': new_state})

    def pack2check(self):
        self.ensure_one()
        assert self.state == 'pack'
        self.write({
            'state': 'check',
            })

    def set_qty_on_lines(self, force_ratio=False):
        """force_ratio=(line_to_force, ratio)
        All pro-rata computation is handled here"""
        self.ensure_one()
        pr_juice = self.env['decimal.precision'].precision_get('Fruit Juice Volume')
        pr_ratio = self.env['decimal.precision'].precision_get('Fruit Juice Ratio')
        total_juice_qty = self.juice_qty
        ctype = self.compensation_type
        if ctype == 'last':
            total_juice_qty -= self.compensation_juice_qty
        total_compensation_juice_qty = False
        if ctype in ('first', 'last'):
            total_compensation_juice_qty = self.compensation_juice_qty
        if force_ratio:
            first_line_to_process = force_ratio[0]
            first_line_ratio = force_ratio[1]
            first_line_juice_qty = first_line_to_process.fruit_qty * first_line_ratio / 100.0
            if float_compare(first_line_juice_qty, total_juice_qty, precision_digits=pr_juice) > 0:
                raise UserError(_(
                    "The forced ratio (%s %% on arrival line %s) is not possible because it would "
                    "attribute more juice than the produced juice.") % (
                        first_line_ratio, first_line_to_process.name))
            total_juice_prorata = total_juice_qty - first_line_juice_qty
            total_fruit_prorata = self.fruit_qty - first_line_to_process.fruit_qty
        else:
            first_line_to_process = self.line_ids[0]
            first_line_ratio = self.ratio
            first_line_juice_qty = first_line_to_process.fruit_qty * total_juice_qty / self.fruit_qty
            total_juice_prorata = total_juice_qty
            total_fruit_prorata = self.fruit_qty
        # The compensation juice qty is distributed pro-rata of the juice_qty ;
        # so the forced ratio is in-directly taken into account
        first_line_compensation_juice_qty = False
        if total_compensation_juice_qty:
            first_line_compensation_juice_qty = total_compensation_juice_qty * first_line_juice_qty / total_juice_qty
        first_line_vals = first_line_to_process.juice_qty_compute_other_vals(
            first_line_juice_qty, first_line_compensation_juice_qty, first_line_ratio)
        # Write on first line
        first_line_to_process.write(first_line_vals)
        lines = [line for line in self.line_ids if line != first_line_to_process]
        for line in lines:
            # compute juice qty with a pro-rata using special values total_juice_prorata
            # and total_fruit_prorata
            juice_qty = line.fruit_qty * total_juice_prorata / total_fruit_prorata
            compensation_juice_qty = False
            juice_qty_for_ratio = juice_qty
            if total_compensation_juice_qty:
                compensation_juice_qty = total_compensation_juice_qty * juice_qty / total_juice_qty
            if ctype == 'first':
                juice_qty_for_ratio += compensation_juice_qty
            ratio = float_round(
                100 * juice_qty_for_ratio / line.fruit_qty, precision_digits=pr_ratio)
            vals = line.juice_qty_compute_other_vals(
                juice_qty, compensation_juice_qty, ratio)
            # Write on other lines
            line.write(vals)

    def compensation_check_tank(self):
        '''Performs check and return the qty of the tank'''
        self.ensure_one()
        ctype = self.compensation_type
        pr_juice = self.env['decimal.precision'].precision_get('Fruit Juice Volume')
        cloc = self.compensation_location_id
        if not cloc:
            if ctype == 'none':
                return 0
            raise UserError(_(
                "The production %s uses compensation, so you must set the "
                "compensation tank.") % self.name)
        cloc.fruit_juice_tank_check(raise_if_not_merged=False, raise_if_empty=False)
        cqty = cloc.fruit_juice_qty
        if ctype in ('last', 'none'):
            # cloc must be empty
            if float_compare(cqty, 0, precision_digits=pr_juice) > 0:
                raise UserError(_(
                    "The production %s uses last of day compensation or no compensation, so the compensation tank must be empty before the operation.") % self.name)
        elif ctype == 'first':
            if float_compare(cqty, 0, precision_digits=pr_juice) <= 0:
                raise UserError(_(
                    "The production %s uses first of day compensation, so the compensation tank mustn't be empty before the operation.") % self.name)
        return cqty

    def check2done(self):
        self.ensure_one()
        assert self.state == 'check'
        splo = self.env['stock.production.lot']
        smo = self.env['stock.move']
        pr_juice = self.env['decimal.precision'].precision_get('Fruit Juice Volume')
        wloc = self.warehouse_id.fruit_withdrawal_loc_id
        stock_loc = self.warehouse_id.lot_stock_id
        sale_loc = self.sale_location_id
        cloc = self.compensation_location_id
        csale_loc = self.compensation_sale_location_id
        juice_product = self.juice_product_id
        season = self.season_id
        to_shrinkage_tank_juice_qty = 0.0
        ctype = self.compensation_type

        self.compensation_check_tank()
        if ctype == 'last':
            if float_compare(self.compensation_juice_qty, 0, precision_digits=pr_juice) <= 0:
                raise UserError(_(
                    "The production %s uses last of day compensation, so the "
                    "'Juice Compensation' should be positive.") % self.name)
        # create prod lot
        # No expiry date on fruit juice in tanks
        prodlot = splo.create({
            'fruit_production_id': self.id,
            'product_id': juice_product.id,
            'name': self.name,
            })
        for line in self.line_ids:
            if float_compare(line.withdrawal_juice_qty, 0, precision_digits=pr_juice) > 0:
                # create move from virtual prod > Withdrawal loc
                wmove = smo.create({
                    'product_id': juice_product.id,
                    'name': _('Fruit juice production %s: juice withdrawal related to arrival line %s') % (self.name, line.name),
                    'location_id': juice_product.property_stock_production.id,
                    'location_dest_id': wloc.id,
                    'product_uom': juice_product.uom_id.id,
                    'origin': self.name,
                    'product_uom_qty': line.withdrawal_juice_qty,
                    'restrict_lot_id': prodlot.id,
                    'restrict_partner_id': line.commercial_partner_id.id,
                    })
                wmove.action_done()
                assert wmove.state == 'done'
                line.withdrawal_move_id = wmove.id
            for extra in line.extra_ids:
                if extra.product_id.tracking and extra.product_id.tracking != 'none':
                    raise UserError(_(
                        "Can't select the product '%s' in extra items of "
                        "line %s because it is tracked by lot or serial.")
                        % (extra.product_id.display_name, line.name))
                # Cannot use 'restrict_partner_id'
                # because it would create a negative quant with owner
                # on src location
                extra_move = smo.create({
                    'product_id': extra.product_id.id,
                    'name': _('Fruit juice production %s: extra item withdrawal related to arrival line %s') % (self.name, line.name),
                    'location_id': stock_loc.id,
                    'location_dest_id': wloc.id,
                    'product_uom': extra.product_id.uom_id.id,
                    'origin': self.name,
                    'product_uom_qty': extra.qty,
                    })
                extra_move.action_done()
                # set owner on quants
                extra_move.sudo().quant_ids.write(
                    {'owner_id': line.commercial_partner_id.id})
                assert extra_move.state == 'done'
            if line.juice_destination == 'withdrawal':
                to_shrinkage_tank_juice_qty += line.shrinkage_juice_qty
        prod_vals = {
            'state': 'done',
            'done_datetime': fields.Datetime.now(),
            }
        # Move to sale tank
        if float_compare(self.to_sale_tank_juice_qty, 0, precision_digits=pr_juice) > 0:
            if not sale_loc:
                raise UserError(_(
                    "Sale tank is not set on juice production %s.") % self.name)
            sale_loc.fruit_juice_tank_check(
                raise_if_not_merged=False, raise_if_empty=False)
            sale_loc.fruit_juice_tank_compatibility_check(juice_product, season)
            sale_move = smo.create({
                'product_id': juice_product.id,
                'name': _('Fruit juice production %s to sale tank') % self.name,
                'location_id': juice_product.property_stock_production.id,
                'location_dest_id': sale_loc.id,
                'product_uom': juice_product.uom_id.id,
                'origin': self.name,
                'product_uom_qty': self.to_sale_tank_juice_qty,
                'restrict_lot_id': prodlot.id,
                })
            sale_move.action_done()
            assert sale_move.state == 'done'
            prod_vals['sale_move_id'] = sale_move.id

        # Compensation LAST move
        if (
                ctype == 'last' and
                float_compare(self.compensation_juice_qty, 0, precision_digits=pr_juice) > 0):
            cmove = smo.create({
                'product_id': juice_product.id,
                'name': _('Fruit juice production %s to compensation tank') % self.name,
                'location_id': juice_product.property_stock_production.id,
                'location_dest_id': cloc.id,
                'product_uom': juice_product.uom_id.id,
                'origin': self.name,
                'product_uom_qty': self.compensation_juice_qty,
                'restrict_lot_id': prodlot.id,
                })
            cmove.action_done()
            assert cmove.state == 'done'
            prod_vals['compensation_last_move_id'] = cmove.id
            cloc.sudo().juice_product_id = juice_product.id

        # Shrinkage move
        if float_compare(to_shrinkage_tank_juice_qty, 0, precision_digits=pr_juice) > 0:
            shrinkage_loc = self.shrinkage_location_id
            if not shrinkage_loc:
                raise UserError(_(
                    "Shrinkage tank is not set on juice production %s.") % self.name)
            # We don't use the juice_product for shrinkage, because we would
            # have several different juice products in the shrinkage tank
            # We use shrinkage_product instead
            shrinkage_product = shrinkage_loc.juice_product_id
            if not shrinkage_product:
                raise UserError(_(
                    "Missing juice product on shrinkage tank %s.")
                    % shrinkage_loc.display_name)
            if not shrinkage_product.shrinkage_prodlot_id:
                raise UserError(_(
                    "Missing shrinkage production lot on product '%s'.")
                    % shrinkage_product.display_name)
            shrinkage_move = smo.create({
                'product_id': shrinkage_product.id,
                'name': _('Fruit Juice Production %s: Shrinkage') % self.name,
                'location_id': shrinkage_product.property_stock_production.id,
                'location_dest_id': shrinkage_loc.id,
                'product_uom': shrinkage_product.uom_id.id,
                'origin': self.name,
                'product_uom_qty': to_shrinkage_tank_juice_qty,
                'restrict_lot_id': shrinkage_product.shrinkage_prodlot_id.id,
                })
            shrinkage_move.action_done()
            prod_vals['shrinkage_move_id'] = shrinkage_move.id
        # Distribute compensation
        if ctype == 'first':
            # In sale and mix, the compensation is always sold
            if all([line.juice_destination in ('sale', 'mix') for line in self.line_ids]):
                # full trf
                if not csale_loc:
                    raise UserError(_(
                        "On juice production %s which has first-of-day "
                        "compensation, you must set a compensation sale tank.") % self.name)
                cloc.fruit_juice_transfer(
                    csale_loc, 'full', self.warehouse_id,
                    origin=_('Empty compensation tank to sale tank'), auto_validate=True)
            else:
                # partial trf
                if float_compare(self.to_compensation_sale_tank_juice_qty, 0, precision_digits=pr_juice) > 0:
                    if not csale_loc:
                        raise UserError(_(
                            "On juice production %s which has first-of-day "
                            "compensation, you must set a compensation sale tank.") % self.name)
                    cloc.fruit_juice_transfer(
                        csale_loc, 'partial', self.warehouse_id,
                        partial_transfer_qty=self.to_compensation_sale_tank_juice_qty,
                        origin=_('Partial transfer of compensation tank to sale tank'),
                        auto_validate=True)
                wlines = [l for l in self.line_ids if l.juice_destination == 'withdrawal']
                origin = _('Transfer of compensation tank to withdrawal location')
                while wlines:
                    # work on 1st line of wlines
                    if len(wlines) == 1:
                        # full trf for the last withdrawal line
                        cloc.fruit_juice_transfer(
                            wloc, 'full', self.warehouse_id,
                            dest_partner=wlines[0].commercial_partner_id,
                            origin=origin, auto_validate=True)
                    else:
                        cloc.fruit_juice_transfer(
                            wloc, 'partial', self.warehouse_id,
                            dest_partner=wlines[0].commercial_partner_id,
                            partial_transfer_qty=wlines[0].compensation_juice_qty,
                            origin=origin, auto_validate=True)

                    # remove first line of wlines
                    wlines.pop(0)
            # DON'T remove juice_product_id on compensation tank
            # because we now go through fruit_tank_type_change()
            # even when compensation = 'none', so the product must always be set
            # cloc.sudo().juice_product_id = False

        self.write(prod_vals)
        self.update_arrival_production_done()

    def update_arrival_production_done(self):
        self.ensure_one()
        oalo = self.env['fruit.arrival.line']
        oao = self.env['fruit.arrival']
        arrivals = oao
        for line in self.line_ids:
            arrivals |= line.arrival_id
        assert arrivals
        arrivals_res = oalo.read_group(
            [('production_state', '=', 'done'), ('arrival_id', 'in', arrivals.ids)],
            ['juice_qty_net', 'fruit_qty', 'arrival_id'],
            ['arrival_id'])
        for arrival_re in arrivals_res:
            arrival = oao.browse(arrival_re['arrival_id'][0])
            fruit_qty_pressed = arrival_re['fruit_qty']
            juice_qty_net = arrival_re['juice_qty_net']
            juice_ratio_net = fruit_ratio_net = 0.0
            if fruit_qty_pressed:
                juice_ratio_net = 100 * juice_qty_net / fruit_qty_pressed
            if juice_qty_net:
                fruit_ratio_net = fruit_qty_pressed / juice_qty_net
            arrival.write({
                'fruit_qty_pressed': fruit_qty_pressed,
                'juice_qty_net': juice_qty_net,
                'juice_ratio_net': juice_ratio_net,
                'fruit_ratio_net': fruit_ratio_net,
                })

    def unlink(self):
        for production in self:
            if production.state == 'done':
                raise UserError(_(
                    "Cannot delete production %s which is in Done state.")
                    % production.name)
        return super(FruitJuiceProduction, self).unlink()

    def detach_lines(self):
        self.ensure_one()
        self.line_ids.write({'production_id': False})
        self.palox_id.juice_product_id = self.juice_product_id.id

    def _compute_day_position(self):
        for prod in self:
            if prod.state == 'cancel':
                day_position = 0
            else:
                # same order as on-screen
                same_day_prod = self.search(
                    [('date', '=', prod.date), ('state', '!=', 'cancel')])
                same_day_reverse_order = [p for p in same_day_prod]
                same_day_reverse_order.reverse()
                index = same_day_reverse_order.index(prod)
                day_position = index + 1
            prod.day_position = day_position

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(FruitJuiceProduction, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        return self.env.user.company_id.current_season_update(res, view_type)
