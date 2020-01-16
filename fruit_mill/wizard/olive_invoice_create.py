# Copyright 2018 Barroux Abbey (https://www.barroux.org/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, _
from odoo.exceptions import UserError


class FruitInvoiceCreate(models.TransientModel):
    _name = 'fruit.invoice.create'
    _description = 'Wizard to create invoices for fruit mill'

    partner_id = fields.Many2one(
        'res.partner', string='Fruit Farmer', required=True,
        domain=[('fruit_farmer', '=', True)])
    fruit_cultivation_form_ko = fields.Boolean(
        related='partner_id.commercial_partner_id.fruit_cultivation_form_ko',
        readonly=True)
    fruit_parcel_ko = fields.Boolean(
        related='partner_id.commercial_partner_id.fruit_parcel_ko', readonly=True)
    fruit_organic_certif_ko = fields.Boolean(
        related='partner_id.commercial_partner_id.fruit_organic_certif_ko',
        readonly=True)
    fruit_invoicing_ko = fields.Boolean(
        related='partner_id.commercial_partner_id.fruit_invoicing_ko',
        readonly=True)
    season_id = fields.Many2one(
        'fruit.season', string='Season', required=True,
        default=lambda self: self.env.user.company_id.current_season_id.id)
    fruit_sale_pricelist_id = fields.Many2one(
        related='partner_id.fruit_sale_pricelist_id',
        readonly=False)
    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Fruit Mill', required=True,
        default=lambda self: self.env.user._default_fruit_mill_wh())
    invoice_type = fields.Selection([
        ('out', 'Customer Invoice'),
        ('in', 'Supplier Invoice'),
        ('all', 'Supplier and Customer Invoice'),
        ], string='Invoice Type', default='all', required=True)

    def validate(self):
        self.ensure_one()
        oalo = self.env['fruit.arrival.line']
        commercial_partner = self.partner_id.commercial_partner_id
        in_invoice = out_invoice = self.env['account.invoice']
        if self.invoice_type in ('in', 'all'):
            lines = oalo.search([
                ('commercial_partner_id', '=', commercial_partner.id),
                ('warehouse_id', '=', self.warehouse_id.id),
                ('season_id', '=', self.season_id.id),
                ('production_state', '=', 'done'),
                ('in_invoice_line_id', '=', False),
                ('juice_destination', 'in', ('sale', 'mix')),
                ('sale_juice_qty', '>', 0),
                ])
            if lines:
                commercial_partner.fruit_check_in_invoice_fiscal_position()
                in_invoice = lines.in_invoice_create()
        if self.invoice_type in ('all', 'out'):
            lines = oalo.search([
                ('commercial_partner_id', '=', commercial_partner.id),
                ('warehouse_id', '=', self.warehouse_id.id),
                ('season_id', '=', self.season_id.id),
                ('production_state', '=', 'done'),
                ('out_invoice_id', '=', False),
                ])
            if lines:
                out_invoice = lines.out_invoice_create()
        if not in_invoice and not out_invoice:
            raise UserError(_("No invoice created"))
        if in_invoice and not out_invoice:
            action = self.env.ref('account.action_invoice_tree2').read()[0]
            action.update({
                'views': [(self.env.ref('account.invoice_supplier_form').id, 'form')],
                'view_mode': 'form,tree,kanban,calendar',
                'res_id': in_invoice.id,
                })
        else:
            action = self.env.ref('account.action_invoice_tree1').read()[0]
            action.update({
                'views': [(self.env.ref('account.invoice_form').id, 'form')],
                'view_mode': 'form,tree,kanban,calendar',
                'res_id': out_invoice.id,
                })
        return action
