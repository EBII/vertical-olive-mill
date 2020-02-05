# Copyright 2018 Barroux Abbey (https://www.barroux.org/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError
import odoo.addons.decimal_precision as dp


class FruitPalox(models.Model):
    _name = 'fruit.palox'
    _description = 'Fruit Palox'
    _order = 'name'

    name = fields.Char(string='Number', required=True)
    label = fields.Char(string='Label')
    company_id = fields.Many2one(
        'res.company', string='Company', ondelete='cascade', required=True,
        default=lambda self: self.env['res.company']._company_default_get())
    borrower_partner_id = fields.Many2one(
        'res.partner', string='Borrower', ondelete='restrict', copy=False,
        domain=[('parent_id', '=', False), ('fruit_farmer', '=', True)])
    borrowed_date = fields.Date('Borrowed Date')
    active = fields.Boolean(default=True)
    production_ids = fields.One2many(
        'fruit.juice.production', 'palox_id', string='Juice Productions')
    arrival_line_ids = fields.One2many(
        'fruit.arrival.line', 'palox_id', string='Arrival Lines')
    # ??? fillup_ok = fields.Boolean(compute='_compute_weight')
    juice_product_id = fields.Many2one(
        'product.product', string='Current Juice Product',
        domain=[('fruit_type', '=', 'juice')])
    empty_weight = fields.Float(
        string='Empty Weight (kg)', digits=dp.get_precision('Fruit Weight'))
    weight = fields.Float(
        compute='_compute_weight', string='Current Net Weight (kg)',
        digits=dp.get_precision('Fruit Weight'), readonly=True)
    juice_destination = fields.Selection([
        ('withdrawal', 'Withdrawal'),
        ('sale', 'Sale'),
        ('mix', 'Mix'),
        ], string='Juice Destination', compute='_compute_other',
        readonly=True)
    farmers = fields.Char(
        string='Farmers', compute='_compute_other', readonly=True)
    arrival_date = fields.Date(
        string='Arrival Date', compute='_compute_other', readonly=True,
        help="If there are multiple arrivals in this palox, this field contains "
        "the oldest arrival date.")
    line_ids = fields.One2many(
        'fruit.arrival.line', 'palox_id', string='Content', readonly=True,
        domain=[('state', '=', 'done'), ('production_id', '=', False)])
    borrow_history_ids = fields.One2many(
        'fruit.palox.borrow.history', 'palox_id', string='Borrow History',
        readonly=True)

    def _compute_weight(self):
        res = self.env['fruit.arrival.line'].read_group([
            ('palox_id', 'in', self.ids),
            ('state', '=', 'done'),
            ('production_id', '=', False),
            ], ['palox_id', 'fruit_qty'], ['palox_id'])
        for re in res:
            self.browse(re['palox_id'][0]).weight = re['fruit_qty']

    # I don't put the 2 compute methods in the same,
    # because name_get() only uses weight, and computation of weight is
    # fast with read_group()
    def _compute_other(self):
        lines = self.env['fruit.arrival.line'].search([
            ('palox_id', 'in', self.ids),
            ('state', '=', 'done'),
            ('production_id', '=', False),
            ])
        paloxes = {}
        for l in lines:
            if l.palox_id not in paloxes:
                paloxes[l.palox_id] = {
                    'juice_dests': [l.juice_destination],
                    'farmers': [l.commercial_partner_id.name],
                    'arrival_date': l.arrival_date,
                    }
            else:
                paloxes[l.palox_id]['juice_dests'].append(l.juice_destination)
                paloxes[l.palox_id]['farmers'].append(l.commercial_partner_id.name)
                if l.arrival_date < paloxes[l.palox_id]['arrival_date']:
                    paloxes[l.palox_id]['arrival_date'] = l.arrival_date
        for palox, rdict in paloxes.items():
            juice_destination = 'mix'
            if all([dest == 'sale' for dest in rdict['juice_dests']]):
                juice_destination = 'sale'
            elif all([dest == 'withdrawal' for dest in rdict['juice_dests']]):
                juice_destination = 'withdrawal'
            palox.juice_destination = juice_destination
            palox.farmers = ' / '.join(rdict['farmers'])
            palox.arrival_date = rdict['arrival_date']

    @api.constrains('borrower_partner_id', 'borrowed_date')
    def palox_check(self):
        for palox in self:
            if (
                    (palox.borrower_partner_id and not palox.borrowed_date) or
                    (not palox.borrower_partner_id and palox.borrowed_date)):
                raise ValidationError(_(
                    "On palox %s, the fields 'Borrower' and 'Borrowed Date' "
                    "should be either both set or both empty.") % palox.name)

    def name_get(self):
        res = []
        for rec in self:
            label = rec.label and ' ' + rec.label or ''
            name = _('%s%s (Current: %s kg%s)') % (rec.name, label, rec.weight, rec.juice_product_id and ' ' + rec.juice_product_id.name or '')
            res.append((rec.id, name))
        return res

    _sql_constraints = [(
        'name_company_unique',
        'unique(name, company_id)',
        'This palox number already exists in this company.')]

    def lend_palox(self, partner):
        assert not partner.parent_id
        self.sudo().write({
            'borrower_partner_id': partner.id,
            'borrowed_date': fields.Date.context_today(self),
            })

    def return_borrowed_palox(self):
        self.ensure_one()
        if not self.borrower_partner_id:
            raise UserError(_(
                "Cannot return palox '%s' because it currently has no borrower.")
                % self.display_name)
        if not self.borrowed_date:
            raise UserError(_(
                "Cannot return palox '%s' because it has no borrowed date.")
                % self.display_name)
        self.env['fruit.palox.borrow.history'].sudo().create({
            'palox_id': self.id,
            'partner_id': self.borrower_partner_id.id,
            'start_date': self.borrowed_date,
            })
        self.sudo().write({
            'borrower_partner_id': False,
            'borrowed_date': False,
            })
        return


class FruitPaloxBorrowHistory(models.Model):
    _name = 'fruit.palox.borrow.history'
    _description = 'Fruit Palox Borrow History'
    _order = 'end_date desc'

    palox_id = fields.Many2one(
        'fruit.palox', string='Palox', required=True, ondelete='cascade',
        readonly=True, index=True)
    partner_id = fields.Many2one(
        'res.partner', string='Borrower', required=True, ondelete='restrict',
        readonly=True)
    start_date = fields.Date(string='Start Date', required=True, readonly=True)
    end_date = fields.Date(
        string='End Date', default=fields.Date.context_today, readonly=True)
    season_id = fields.Many2one(
        'fruit.season', readonly=True, string='Season',
        default=lambda self: self.env.user.company_id.current_season_id.id)
    company_id = fields.Many2one(
        related='palox_id.company_id', readonly=True, store=True)
