# Copyright 2018 Barroux Abbey (https://www.barroux.org/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp


class ResPartner(models.Model):
    _inherit = 'res.partner'

    fruit_farmer = fields.Boolean('Fruit Farmer')
    fruit_ochard_ids = fields.One2many(
        'fruit.ochard', 'partner_id', string='Fruit Ochards')
    fruit_tree_total = fields.Integer(
        compute='_compute_fruit_total', string='Total Trees', readonly=True)
    fruit_area_total = fields.Float(
        compute='_compute_fruit_total', string='Total Area', readonly=True,
        digits=dp.get_precision('Fruit Parcel Area'))
    fruit_lended_palox = fields.Integer(
        compute='_compute_fruit_total', string='Lended Palox', readonly=True)
    fruit_lended_regular_case = fields.Integer(
        compute='_compute_fruit_total', string='Lended Regular Case', readonly=True)
    fruit_lended_organic_case = fields.Integer(
        compute='_compute_fruit_total', string='Lended Organic Case', readonly=True)
    fruit_current_season_id = fields.Many2one(
        'fruit.season', compute='_compute_fruit_total', readonly=True,
        string='Current Fruit Season')
    fruit_qty_current_season = fields.Float(
        compute='_compute_fruit_total', string='Fruit Qty Brought',
        readonly=True, digits=dp.get_precision('Fruit Weight'),
        help="Fruits brought for the current season in kg")
    fruit_qty_triturated_current_season = fields.Float(
        compute='_compute_fruit_total', string='Fruit Qty Triturated',
        readonly=True, digits=dp.get_precision('Fruit Weight'),
        help="Fruits triturated for the current season in kg")
    fruit_juice_qty_current_season = fields.Float(
        compute='_compute_fruit_total', string='Net Juice Qty', readonly=True,
        digits=dp.get_precision('Fruit Juice Volume'),
        help="Net fruit juice producted for the current season in liters")
    fruit_juice_ratio_current_season = fields.Float(
        compute='_compute_fruit_total', string='Net Juice Ratio', readonly=True,
        digits=dp.get_precision('Fruit Juice Ratio'),
        help="Net juice ratio for the current season in percentage")
    fruit_juice_qty_withdrawal_current_season = fields.Float(
        compute='_compute_fruit_total', string='Withdrawal Juice Qty', readonly=True,
        digits=dp.get_precision('Fruit Juice Volume'),
        help="Withdrawal juice (already withdrawn and pending withdrawal) for the current season in liters")
    fruit_juice_qty_to_withdraw = fields.Float(
        compute='_compute_fruit_total', string='Juice Qty to Withdraw', readonly=True,
        digits=dp.get_precision('Fruit Juice Volume'),
        help="Fruit juice to withdraw in liters")
    fruit_juice_qty_withdrawn_current_season = fields.Float(
        compute='_compute_fruit_total', string='Withdrawn Juice Qty', readonly=True,
        digits=dp.get_precision('Fruit Juice Volume'),
        help="Withdrawn juice for the current season in liters")
    fruit_sale_juice_qty_current_season = fields.Float(
        compute='_compute_fruit_total', string='Juice Qty Sold', readonly=True,
        digits=dp.get_precision('Fruit Juice Volume'),
        help="Sold fruit juice for the current season in liters")
    fruit_cultivation_form_ko = fields.Boolean(
        compute='_compute_organic_and_warnings',
        string='Cultivation Form Missing', readonly=True)
    fruit_parcel_ko = fields.Boolean(
        compute='_compute_organic_and_warnings',
        string='Parcel Information Incomplete', readonly=True)
    fruit_organic_certif_ko = fields.Boolean(
        compute='_compute_organic_and_warnings',
        string='Organic Certification Missing', readonly=True)
    fruit_invoicing_ko = fields.Boolean(
        compute='_compute_organic_and_warnings',
        string='Invoicing to do', readonly=True)
    fruit_organic_certification_ids = fields.One2many(
        'partner.organic.certification', 'partner_id', 'Organic Certifications')
    fruit_culture_type = fields.Selection([
        ('regular', 'Regular'),
        ('organic', 'Organic'),
        ('conversion', 'Conversion'),
        ], compute='_compute_organic_and_warnings',
        string='Fruit Culture Type', readonly=True)
    fruit_organic_certified_logo = fields.Binary(
        compute='_compute_organic_and_warnings',
        string='Organic Certified Logo', readonly=True)
    fruit_sale_pricelist_id = fields.Many2one(
        'fruit.sale.pricelist', string='Sale Pricelist for Fruit Mill',
        company_dependent=True)

    @api.onchange('fruit_farmer')
    def fruit_farmer_change(self):
        if self.fruit_farmer:
            self.customer = True
            self.supplier = True

    @api.one
    def _compute_fruit_total(self):
        fruit_lended_regular_case = 0
        fruit_lended_organic_case = 0
        fruit_lended_palox = 0
        fruit_tree_total = 0
        fruit_area_total = 0.0
        fruit_qty_current_season = 0.0
        fruit_current_season_id = False
        fruit_qty_triturated_current_season = 0.0
        fruit_sale_juice_qty_current_season = 0.0
        fruit_juice_qty_current_season = 0.0
        fruit_juice_qty_withdrawal_current_season = 0.0
        fruit_juice_ratio_current_season = 0.0
        fruit_juice_qty_to_withdraw = 0.0
        fruit_juice_qty_withdrawn_current_season = 0.0
        if self.fruit_farmer:
            company = self.env.user.company_id
            cases_res = self.env['fruit.lended.case'].read_group([
                ('company_id', '=', company.id),
                ('partner_id', '=', self.id)],
                ['regular_qty', 'organic_qty'], [])
            if cases_res:
                fruit_lended_regular_case = cases_res[0]['regular_qty'] or 0
                fruit_lended_organic_case = cases_res[0]['organic_qty'] or 0
            fruit_lended_palox = self.env['fruit.palox'].search([
                ('borrower_partner_id', '=', self.id),
                ('company_id', '=', company.id),
                ], count=True)

            parcel_res = self.env['fruit.parcel'].read_group([
                ('partner_id', '=', self.id)],
                ['tree_qty', 'area'], [])
            if parcel_res:
                fruit_tree_total = parcel_res[0]['tree_qty'] or 0.0
                fruit_area_total = parcel_res[0]['area'] or 0.0

            season_id = self._context.get('season_id')
            if not season_id:
                season = self.env['fruit.season'].get_current_season()
                if season:
                    season_id = season.id

            if season_id:
                fruit_current_season_id = season_id
                arrival_res = self.env['fruit.arrival.line'].read_group([
                    ('season_id', '=', season_id),
                    ('commercial_partner_id', '=', self.id),
                    ('state', '=', 'done')],
                    ['fruit_qty'], [])
                if arrival_res:
                    fruit_qty_current_season = arrival_res[0]['fruit_qty'] or 0.0
                arrival_prod_res = self.env['fruit.arrival.line'].read_group([
                    ('season_id', '=', season_id),
                    ('commercial_partner_id', '=', self.id),
                    ('state', '=', 'done'),
                    ('production_state', '=', 'done')],
                    ['fruit_qty', 'sale_juice_qty', 'juice_qty_net', 'withdrawal_juice_qty_with_compensation'],
                    [])
                if arrival_prod_res:
                    fruit_qty_triturated_current_season = arrival_prod_res[0]['fruit_qty'] or 0.0
                    fruit_sale_juice_qty_current_season = arrival_prod_res[0]['sale_juice_qty'] or 0.0
                    fruit_juice_qty_current_season = arrival_prod_res[0]['juice_qty_net'] or 0.0
                    fruit_juice_qty_withdrawal_current_season = arrival_prod_res[0]['withdrawal_juice_qty_with_compensation'] or 0.0
                    if fruit_qty_triturated_current_season:
                        fruit_juice_ratio_current_season = 100 * fruit_juice_qty_current_season / fruit_qty_triturated_current_season
            fruit_products = self.env['product.product'].search([
                ('fruit_type', '=', 'juice')])
            withdrawal_locations = self.env['stock.location'].search([
                ('fruit_tank_type', '=', False), ('usage', '=', 'internal')])
            withdrawal_res = self.env['stock.quant'].read_group([
                ('location_id', 'in', withdrawal_locations.ids),
                ('product_id', 'in', fruit_products.ids),
                ('owner_id', '=', self.id)],
                ['quantity'], [])

            if withdrawal_res:
                fruit_juice_qty_to_withdraw = withdrawal_res[0]['quantity'] or 0.0
            fruit_juice_qty_withdrawn_current_season = fruit_juice_qty_withdrawal_current_season - fruit_juice_qty_to_withdraw
        self.fruit_lended_regular_case = fruit_lended_regular_case
        self.fruit_lended_organic_case = fruit_lended_organic_case
        self.fruit_lended_palox = fruit_lended_palox
        self.fruit_tree_total = fruit_tree_total
        self.fruit_area_total = fruit_area_total
        self.fruit_qty_current_season = fruit_qty_current_season
        self.fruit_current_season_id = fruit_current_season_id
        self.fruit_qty_triturated_current_season = fruit_qty_triturated_current_season
        self.fruit_sale_juice_qty_current_season = fruit_sale_juice_qty_current_season
        self.fruit_juice_qty_current_season = fruit_juice_qty_current_season
        self.fruit_juice_qty_withdrawal_current_season = fruit_juice_qty_withdrawal_current_season
        self.fruit_juice_ratio_current_season = fruit_juice_ratio_current_season
        self.fruit_juice_qty_to_withdraw = fruit_juice_qty_to_withdraw
        self.fruit_juice_qty_withdrawn_current_season = fruit_juice_qty_withdrawn_current_season

    def _compute_organic_and_warnings(self):
        poco = self.env['partner.organic.certification']
        oco = self.env['fruit.cultivation']
        ooo = self.env['fruit.ochard']
        opo = self.env['fruit.parcel']
        oalo = self.env['fruit.arrival.line']
        parcel_required_fields = [
            'ochard_id',
            'land_registry_ref',
            'area',
            'tree_qty',
            'variant_label',
            # 'density', no warning if empty
            'planted_year',
            # 'irrigation', no warning if empty
            # 'cultivation_method', no warning if empty
            ]
        for partner in self:
            culture_type = 'regular'
            filename = False
            logo = False
            cultivation_form_ko = True
            parcel_ko = True
            certif_ko = False
            invoicing_ko = False
            if partner.fruit_farmer and not partner.parent_id:
                # parcel_ok if all ochards have at least one parcel
                # and alls parcels have complete info
                ochard_ids = ooo.search([('partner_id', '=', partner.id)]).ids
                if ochard_ids:
                    parcels_complete = True
                    parcels = opo.search_read(
                        [('partner_id', '=', partner.id)],
                        parcel_required_fields)
                    for parcel in parcels:
                        if parcel.get('ochard_id'):
                            ochard_id = parcel['ochard_id'][0]
                            if ochard_id in ochard_ids:
                                ochard_ids.remove(ochard_id)
                        for pfield in parcel_required_fields:
                            if not parcel.get(pfield):
                                parcels_complete = False
                                break
                        if not parcels_complete:
                            break
                    if not ochard_ids and parcels_complete:
                        parcel_ko = False

                season_id = self._context.get('season_id')
                if not season_id:
                    season = self.env['fruit.season'].get_current_season()
                    if season:
                        season_id = season.id

                if season_id:
                    cert = poco.search([
                        ('partner_id', '=', partner.id),
                        ('season_id', '=', season_id),
                        ], limit=1)
                    if cert:
                        if cert.conversion:
                            culture_type = 'conversion'
                            filename = 'organic_logo_conversion_done.png'
                            if cert.state == 'draft':
                                filename = 'organic_logo_conversion_draft.png'
                        else:
                            culture_type = 'organic'
                            filename = 'organic_logo_done.png'
                            if cert.state == 'draft':
                                filename = 'organic_logo_draft.png'
                    if cert.state == 'draft':
                        certif_ko = True

                    cultivations = oco.search([
                        ('season_id', '=', season_id),
                        ('partner_id', '=', partner.id)], limit=1)
                    if cultivations:
                        cultivation_form_ko = False
                    lines_to_out_invoice = oalo.search([
                        ('commercial_partner_id', '=', partner.id),
                        ('season_id', '=', season_id),
                        ('production_state', '=', 'done'),
                        ('out_invoice_id', '=', False),
                        ], count=True)
                    if lines_to_out_invoice:
                        invoicing_ko = True
                    else:
                        lines_to_in_invoice = oalo.search([
                            ('commercial_partner_id', '=', partner.id),
                            ('production_state', '=', 'done'),
                            ('in_invoice_line_id', '=', False),
                            ('juice_destination', 'in', ('sale', 'mix')),
                            ('sale_juice_qty', '>', 0),
                            ('season_id', '=', season_id),
                            ], count=True)
                        if lines_to_in_invoice:
                            invoicing_ko = True
            if filename:
                fname_path = 'fruit_mill/static/image/%s' % filename
                f = tools.file_open(fname_path, 'rb')
                f_binary = f.read()
                if f_binary:
                    logo = f_binary.encode('base64')
            partner.fruit_culture_type = culture_type
            partner.fruit_organic_certified_logo = logo
            partner.fruit_cultivation_form_ko = cultivation_form_ko
            partner.fruit_parcel_ko = parcel_ko
            partner.fruit_organic_certif_ko = certif_ko
            partner.fruit_invoicing_ko = invoicing_ko

    def fruit_check_in_invoice_fiscal_position(self):
        self.ensure_one()
        assert not self.parent_id
        if not self.vat and not self.property_account_position_id:
            raise UserError(_(
                "You are about to generate a supplier invoice for "
                "farmer '%s': you must enter his VAT number in Odoo "
                "or set a fiscal position corresponding to his "
                "fiscal situation (otherwise, we would "
                "purchase fruit juice with VAT to a farmer "
                "that is not subject to VAT, which would be a big "
                "problem!).") % self.display_name)

    def update_organic_certif(self):
        self.ensure_one()
        cert = self.env['partner.organic.certification'].search([
            ('partner_id', '=', self.id),
            ('season_id', '=', self.env.user.company_id.current_season_id.id),
            ('state', '=', 'draft'),
            ], limit=1)
        action = self.env.ref('fruit_mill.partner_organic_certification_action').read()[0]
        action['context'] = {
            'partner_organic_certification_main_view': True,
            'search_default_partner_id': self.id,
            'default_partner_id': self.id,
            }
        if cert:
            action.update({
                'view_mode': 'form,tree',
                'res_id': cert.id,
                'views': False,
                })
        return action

    def create_single_fruit_ochard(self):
        self.ensure_one()
        assert not self.parent_id
        assert not self.fruit_ochard_ids
        self.env['fruit.ochard'].create({
            'partner_id': self.id,
            'name': _('OCHARD TO RENAME'),
            })
