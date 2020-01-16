# Copyright 2019 Barroux Abbey (https://www.barroux.org/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError


class OliveAgrimerReport(models.Model):
    _name = 'olive.agrimer.report'
    _inherit = ['mail.thread']
    _description = 'Olive ARGIMER reports'
    _order = 'date_start desc'
    _rec_name = 'date_start'

    company_id = fields.Many2one(
        'res.company', string='Company',
        ondelete='cascade', required=True,
        states={'done': [('readonly', True)]},
        default=lambda self: self.env['res.company']._company_default_get())
    date_range_id = fields.Many2one(
        'date.range', string='Date Range',
        states={'done': [('readonly', True)]})
    date_start = fields.Date(
        string='Start Date', required=True, track_visibility='onchange',
        states={'done': [('readonly', True)]})
    date_end = fields.Date(
        string='End Date', track_visibility='onchange',
        required=True, states={'done': [('readonly', True)]})
    olive_arrival_qty = fields.Float(
        string='Olive Arrival (kg)', digits=dp.get_precision('Olive Weight'),
        states={'done': [('readonly', True)]})
    olive_pressed_qty = fields.Float(
        string='Olive Pressed (kg)', digits=dp.get_precision('Olive Weight'),
        states={'done': [('readonly', True)]})
    organic_virgin_juice_produced = fields.Float(
        string='Organic Virgin Olive Juice Produced (L)',
        digits=dp.get_precision('Olive Juice Volume'),
        states={'done': [('readonly', True)]})
    organic_extravirgin_juice_produced = fields.Float(
        string='Organic Extra Virgin Olive Juice Produced (L)',
        digits=dp.get_precision('Olive Juice Volume'),
        states={'done': [('readonly', True)]})
    regular_virgin_juice_produced = fields.Float(
        string='Regular Virgin Olive Juice Produced (L)',
        digits=dp.get_precision('Olive Juice Volume'),
        states={'done': [('readonly', True)]})
    regular_extravirgin_juice_produced = fields.Float(
        string='Regular Extra Virgin Olive Juice Produced (L)',
        digits=dp.get_precision('Olive Juice Volume'),
        states={'done': [('readonly', True)]})
    # Juice OUT
    # Shrinkage
    shrinkage_organic_virgin_juice = fields.Float(
        string='Shrinkage Organic Virgin Juice (L)',
        digits=dp.get_precision('Olive Juice Volume'),
        states={'done': [('readonly', True)]})
    shrinkage_organic_extravirgin_juice = fields.Float(
        string='Shrinkage Organic Extra Virgin Juice (L)',
        digits=dp.get_precision('Olive Juice Volume'),
        states={'done': [('readonly', True)]})
    shrinkage_regular_virgin_juice = fields.Float(
        string='Shrinkage Regular Virgin Juice (L)',
        digits=dp.get_precision('Olive Juice Volume'),
        states={'done': [('readonly', True)]})
    shrinkage_regular_extravirgin_juice = fields.Float(
        string='Shrinkage Regular Extra Virgin Juice (L)',
        digits=dp.get_precision('Olive Juice Volume'),
        states={'done': [('readonly', True)]})
    # WITHDRAWAL (product = juice /
    # selected source location wh.olive_withdrawal_loc_id)
    withdrawal_organic_virgin_juice = fields.Float(
        string='Withdrawal Organic Virgin Juice (L)',
        digits=dp.get_precision('Olive Juice Volume'),
        states={'done': [('readonly', True)]})
    withdrawal_organic_extravirgin_juice = fields.Float(
        string='Organic Extra Virgin Juice Withdrawal (L)',
        digits=dp.get_precision('Olive Juice Volume'),
        states={'done': [('readonly', True)]})
    withdrawal_regular_virgin_juice = fields.Float(
        string='Regular Virgin Juice Withdrawal (L)',
        digits=dp.get_precision('Olive Juice Volume'),
        states={'done': [('readonly', True)]})
    withdrawal_regular_extravirgin_juice = fields.Float(
        string='Regular Extra Virgin Juice Withdrawal (L)',
        digits=dp.get_precision('Olive Juice Volume'),
        states={'done': [('readonly', True)]})
    # CONSUMER sale (product = bottles /
    # no partner or partner with other pricelists)
    # we don't use fiscal positions, because the fp 'import/export dom-tom' can
    # we used both for B2C and B2B
    sale_consumer_organic_virgin_juice = fields.Float(
        string='Sale to Consumers of Organic Virgin Juice (L)',
        digits=dp.get_precision('Olive Juice Volume'),
        states={'done': [('readonly', True)]})
    sale_consumer_organic_extravirgin_juice = fields.Float(
        string='Sale to Consumers of Organic Extra Virgin Juice (L)',
        digits=dp.get_precision('Olive Juice Volume'),
        states={'done': [('readonly', True)]})
    sale_consumer_regular_virgin_juice = fields.Float(
        string='Sale to Consumers of Regular Virgin Juice (L)',
        digits=dp.get_precision('Olive Juice Volume'),
        states={'done': [('readonly', True)]})
    sale_consumer_regular_extravirgin_juice = fields.Float(
        string='Sale to Consumers of Regular Extra Virgin Juice (L)',
        digits=dp.get_precision('Olive Juice Volume'),
        states={'done': [('readonly', True)]})
    # DISTRIBUTOR sale (product = bottles / partner with selected pricelist)
    sale_distributor_organic_virgin_juice = fields.Float(
        string='Sale to Distributors of Organic Virgin Juice (L)',
        digits=dp.get_precision('Olive Juice Volume'),
        states={'done': [('readonly', True)]})
    sale_distributor_organic_extravirgin_juice = fields.Float(
        string='Sale to Distributors of Organic Extra Virgin Juice (L)',
        digits=dp.get_precision('Olive Juice Volume'),
        states={'done': [('readonly', True)]})
    sale_distributor_regular_virgin_juice = fields.Float(
        string='Sale to Distributors of Regular Virgin Juice (L)',
        digits=dp.get_precision('Olive Juice Volume'),
        states={'done': [('readonly', True)]})
    sale_distributor_regular_extravirgin_juice = fields.Float(
        string='Sale to Distributors of Regular Extra Virgin Juice (L)',
        digits=dp.get_precision('Olive Juice Volume'),
        states={'done': [('readonly', True)]})
    # LOOSE sale (product = juice / all other source locations)
    sale_loose_organic_virgin_juice = fields.Float(
        string='Loose Sale of Organic Virgin Juice (L)',
        digits=dp.get_precision('Olive Juice Volume'),
        states={'done': [('readonly', True)]})
    sale_loose_organic_extravirgin_juice = fields.Float(
        string='Loose Sale of Organic Extra Virgin Juice (L)',
        digits=dp.get_precision('Olive Juice Volume'),
        states={'done': [('readonly', True)]})
    sale_loose_regular_virgin_juice = fields.Float(
        string='Loose Sale of Regular Virgin Juice (L)',
        digits=dp.get_precision('Olive Juice Volume'),
        states={'done': [('readonly', True)]})
    sale_loose_regular_extravirgin_juice = fields.Float(
        string='Loose Sale of Regular Extra Virgin Juice (L)',
        digits=dp.get_precision('Olive Juice Volume'),
        states={'done': [('readonly', True)]})

    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ], default='draft', readonly=True, track_visibility='onchange')

    _sql_constraints = [(
        'date_company_uniq',
        'unique(date_start, date_end, company_id)',
        'An AgriMer report with the same start/end date already exists!')]

    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        if self.date_range_id:
            self.date_start = self.date_range_id.date_start
            self.date_end = self.date_range_id.date_end

    def draft2done(self):
        self.ensure_one()
        assert self.state == 'draft'
        self.state = 'done'

    def back2draft(self):
        self.ensure_one()
        assert self.state == 'done'
        self.state = 'draft'

    def _compute_olive_arrival_qty(self, vals):
        rg = self.env['olive.arrival.line'].read_group([
            ('arrival_date', '>=', self.date_start),
            ('arrival_date', '<=', self.date_end),
            ('arrival_state', '=', 'done'),
            ('company_id', '=', self.company_id.id),
            ], ['olive_qty'], [])
        vals['olive_arrival_qty'] = rg and rg[0]['olive_qty'] or 0.0

    def _compute_olive_pressed_qty(self, vals):
        rg = self.env['olive.arrival.line'].read_group([
            ('production_date', '>=', self.date_start),
            ('production_date', '<=', self.date_end),
            ('production_state', '=', 'done'),
            ('company_id', '=', self.company_id.id),
            ], ['olive_qty'], [])
        vals['olive_pressed_qty'] = rg and rg[0]['olive_qty'] or 0.0

    def _compute_juice_produced(self, vals, juicetype2juiceproducts):
        for juice_type, juice_products in list(juicetype2juiceproducts.items()):
            net_fieldname = '%s_juice_produced' % juice_type
            shrinkage_fieldname = 'shrinkage_%s_juice' % juice_type
            rg = self.env['olive.arrival.line'].read_group([
                ('juice_product_id', 'in', juice_products.ids),
                ('production_date', '>=', self.date_start),
                ('production_date', '<=', self.date_end),
                ('production_state', '=', 'done'),
                ('company_id', '=', self.company_id.id),
                ], ['juice_qty_net', 'shrinkage_juice_qty'], [])
            vals[net_fieldname] = rg and rg[0]['juice_qty_net'] or 0.0
            vals[shrinkage_fieldname] =\
                rg and rg[0]['shrinkage_juice_qty'] or 0.0

    def _compute_juice_out(
            self, vals, juicetype2juiceproducts, bottle2juicetypevol):
        smo = self.env['stock.move']
        move_common_domain = [
            ('state', '=', 'done'),
            ('date', '>=', self.date_start + ' 00:00:00'),
            ('date', '<=', self.date_end + ' 23:59:59'),
            ('company_id', '=', self.company_id.id),
            ]
        # Withdrawal
        olive_whs = self.env['stock.warehouse'].search([
            ('olive_mill', '=', True),
            ('olive_withdrawal_loc_id', '!=', False),
            ('company_id', '=', self.company_id.id)])
        withdrawal_locs = self.env['stock.location']
        for olive_wh in olive_whs:
            withdrawal_locs += olive_wh.olive_withdrawal_loc_id
        for juice_type, juice_products in list(juicetype2juiceproducts.items()):
            move_rg = smo.read_group(
                move_common_domain + [
                    ('product_id', 'in', juice_products.ids),
                    ('location_id', 'in', withdrawal_locs.ids),
                    ('location_dest_id.usage', '=', 'customer'),
                ], ['product_uom_qty'], [])
            return_move_rg = smo.read_group(
                move_common_domain + [
                    ('product_id', 'in', juice_products.ids),
                    ('location_id.usage', '=', 'customer'),
                    ('location_dest_id', 'in', withdrawal_locs.ids),
                ], ['product_uom_qty'], [])
            qty = move_rg and move_rg[0]['product_uom_qty'] or 0.0
            return_qty = return_move_rg and\
                return_move_rg[0]['product_uom_qty'] or 0.0
            withdrawal_fieldname = 'withdrawal_%s_juice' % juice_type
            vals[withdrawal_fieldname] = qty - return_qty
        # Loose
        for juice_type, juice_products in list(juicetype2juiceproducts.items()):
            move_rg = smo.read_group(
                move_common_domain + [
                    ('product_id', 'in', juice_products.ids),
                    ('location_id', 'not in', withdrawal_locs.ids),
                    ('location_dest_id.usage', '=', 'customer'),
                ], ['product_uom_qty'], [])
            return_move_rg = smo.read_group(
                move_common_domain + [
                    ('product_id', 'in', juice_products.ids),
                    ('location_id.usage', '=', 'customer'),
                    ('location_dest_id', 'not in', withdrawal_locs.ids),
                ], ['product_uom_qty'], [])
            loose_fieldname = 'sale_loose_%s_juice' % juice_type
            qty = move_rg and move_rg[0]['product_uom_qty'] or 0.0
            return_qty = return_move_rg and\
                return_move_rg[0]['product_uom_qty'] or 0.0
            vals[loose_fieldname] = qty - return_qty
        # Sale bottles
        rpo = self.env['res.partner']
        distri_pricelists = self.env['product.pricelist'].search([
            ('olive_juice_distributor', '=', True)])

        for bottle, props in list(bottle2juicetypevol.items()):
            move_rg = smo.read_group(
                move_common_domain + [
                    ('product_id', '=', bottle.id),
                    ('location_id.usage', '=', 'internal'),
                    ('location_dest_id.usage', '=', 'customer'),
                ], ['product_uom_qty', 'partner_id'], ['partner_id'])
            return_move_rg = smo.read_group(
                move_common_domain + [
                    ('product_id', '=', bottle.id),
                    ('location_id.usage', '=', 'customer'),
                    ('location_dest_id.usage', '=', 'internal'),
                ], ['product_uom_qty', 'partner_id'], ['partner_id'])
            for return_r in return_move_rg:
                return_r['product_uom_qty'] *= -1
            for r in move_rg + return_move_rg:
                product_qty = r['product_uom_qty']
                if r['partner_id'] and distri_pricelists:
                    partner = rpo.browse(r['partner_id'][0])
                    if (
                            partner.property_product_pricelist and
                            partner.property_product_pricelist in
                            distri_pricelists):
                        self._juice_out_sale_final_compute(
                            'distributor', vals, props, product_qty)
                    else:
                        self._juice_out_sale_final_compute(
                            'consumer', vals, props, product_qty)
                else:
                    self._juice_out_sale_final_compute(
                        'consumer', vals, props, product_qty)

    def _juice_out_sale_final_compute(
            self, partner_type, vals, props, product_qty):
        for juice_type, vol in list(props.items()):
            fieldname = 'sale_%s_%s_juice' % (partner_type, juice_type)
            vals[fieldname] += product_qty * vol

    def report_compute_values(self):
        juice_product_domain = {
            'organic_virgin': [
                ('olive_juice_type', '=', 'virgin'),
                ('olive_culture_type', 'in', ('organic', 'conversion'))],
            'organic_extravirgin': [
                ('olive_juice_type', '=', 'extravirgin'),
                ('olive_culture_type', 'in', ('organic', 'conversion'))],
            'regular_virgin': [
                ('olive_juice_type', '=', 'virgin'),
                ('olive_culture_type', '=', 'regular')],
            'regular_extravirgin': [
                ('olive_juice_type', '=', 'extravirgin'),
                ('olive_culture_type', '=', 'regular')],
            }
        juicetype2juiceproducts = {}
        bottle2juicetypevol = {}
        ppo = self.env['product.product']
        for juice_type, domain in list(juice_product_domain.items()):
            juicetype2juiceproducts[juice_type] = ppo.search(
                domain + [('olive_type', '=', 'juice')])
        regular_bottles = ppo.search([('olive_type', '=', 'bottle_full')])
        for bottle in regular_bottles:
            bom, juice_product, bottle_volume =\
                bottle.juice_bottle_full_get_bom_and_juice_product()
            if not juice_product.olive_juice_type:
                raise UserError(_(
                    "Juice type not configured on juice product '%s'.")
                    % juice_product.display_name)
            if not juice_product.olive_culture_type:
                raise UserError(_(
                    "Culture type not configured on juice product '%s'.")
                    % juice_product.display_name)
            culture_type = juice_product.olive_culture_type
            if culture_type == 'conversion':
                culture_type = 'organic'
            juice_type = '%s_%s' % (culture_type, juice_product.olive_juice_type)
            bottle2juicetypevol[bottle] = {juice_type: bottle_volume}

        pack_bottles = ppo.search([('olive_type', '=', 'bottle_full_pack')])
        for pbottle in pack_bottles:
            bottle2juicetypevol[pbottle] = {}
            pack_dict = pbottle.juice_bottle_full_pack_get_bottles()
            for cbottle, qty in list(pack_dict.items()):
                juice_type, bottle_volume = list(bottle2juicetypevol[cbottle].items())[0]
                if juice_type in bottle2juicetypevol[pbottle]:
                    bottle2juicetypevol[pbottle][juice_type] += bottle_volume * qty
                else:
                    bottle2juicetypevol[pbottle][juice_type] = bottle_volume * qty

        vals = {}
        self._reset_values(vals)
        self._compute_olive_arrival_qty(vals)
        self._compute_olive_pressed_qty(vals)
        self._compute_juice_produced(vals, juicetype2juiceproducts)
        self._compute_juice_out(
            vals, juicetype2juiceproducts, bottle2juicetypevol)
        return vals

    def _reset_values(self, vals):
        ffields = self.env['ir.model.fields'].search([
            ('model', '=', self._name),
            ('ttype', '=', 'float')])
        for ffield in ffields:
            vals[ffield.name] = 0.0

    def generate_report(self):
        vals = self.report_compute_values()
        self.write(vals)
        self.message_post(_("AgriMer report generated."))

    def olive_stock_levels(self, vals):
        vals['olive_stock_start']
