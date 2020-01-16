# Copyright 2018 Barroux Abbey (https://www.barroux.org/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    fruit_type = fields.Selection([
        # Fruits are not handled as products
        ('juice', 'Fruit Juice'),
        ('bottle', 'Empty Juice Bottle'),
        ('bottle_full', 'Full Juice Bottle'),
        ('bottle_full_pack', 'Pack of Full Juice Bottles'),
        ('analysis', 'Analysis'),
        ('extra_service', 'Extra Service'),
        ('service', 'Production Service'),
        ('tax', 'Federation Tax'),
        ], string='Fruit Type')
    fruit_culture_type = fields.Selection([
        ('regular', 'Regular'),
        ('organic', 'Organic'),
        ('conversion', 'Conversion'),
        ], string='Culture Type')
    fruit_bottle_free_full = fields.Boolean(
        string="Not Invoiced when Full")
    fruit_invoice_service_ids = fields.Many2many(
        'product.product', 'product_template_fruit_invoice_service_rel',
        'product_tmpl_id', 'product_id',
        string='Extra Production Services To Invoice',
        domain=[('fruit_type', '=', 'service')])
    fruit_analysis_uom = fields.Char(
        string='Unit of Measure of the Fruit Juice Analysis')
    fruit_analysis_decimal_precision = fields.Integer(
        string='Fruit Juice Analysis Decimal Precision',
        default=1)
    fruit_analysis_instrument = fields.Char(
        string='Instrument used for the Fruit Juice Analysis')
    fruit_analysis_precision = fields.Char(
        string='Precision of the Fruit Juice Analysis')

    _sql_constraints = [(
        'fruit_analysis_decimal_precision_positive',
        'CHECK(fruit_analysis_decimal_precision >= 0)',
        'The decimal precision of the fruit juice analysis must be positive.')]

    # DUPLICATED in product product
    @api.onchange('fruit_type')
    def fruit_type_change(self):
        liter_uom = self.env.ref('uom.product_uom_litre')
        if self.fruit_type == 'juice':
            if self.uom_id != liter_uom:
                self.uom_id = liter_uom
                self.uom_po_id = liter_uom
            self.tracking = 'lot'
        elif self.fruit_type == 'bottle_full':
            self.tracking = 'lot'
        if self.fruit_type in ('service', 'extra_service', 'tax'):
            self.type = 'service'
        elif self.fruit_type == 'analysis':
            self.type == 'consu'
        if not self.fruit_type:
            self.fruit_culture_type = False

    @api.constrains('fruit_type', 'uom_id', 'fruit_culture_type', 'type')
    def check_fruit_type(self):
        liter_uom = self.env.ref('uom.product_uom_litre')
        unit_categ_uom = self.env.ref('uom.product_uom_categ_unit')
        for pt in self:
            if pt.fruit_type == 'juice':
                if not pt.fruit_culture_type:
                    raise ValidationError(_(
                        "Product '%s' has an Fruit Type 'Fruit Juice', so a "
                        "culture type must also be configured.")
                        % pt.display_name)
                if pt.uom_id != liter_uom:
                    raise ValidationError(_(
                        "Product '%s' has an Fruit Type 'Fruit Juice' that "
                        "require 'Liter' as it's unit of measure "
                        "(current unit of measure is %s).")
                        % (pt.display_name, pt.uom_id.display_name))
                if pt.tracking != 'lot':
                    raise ValidationError(_(
                        "Product '%s' has an Fruit Type 'Juice' that require "
                        "tracking by lots.") % pt.display_name)
            if pt.fruit_type == 'bottle_full' and pt.tracking != 'lot':
                raise ValidationError(_(
                    "Product '%s' has an Fruit Type 'Full Juice Bottle' "
                    "that require tracking by lots.") % pt.display_name)
            if (
                    pt.fruit_type in ('bottle', 'bottle_full', 'analysis') and
                    pt.uom_id.category_id != unit_categ_uom):
                raise ValidationError(_(
                    "Product '%s' has an Fruit Type 'Bottle' or 'Analysis' "
                    "that require a unit of measure that belong to the "
                    "'Unit' category (current unit of measure: %s).")
                    % (pt.display_name, pt.uom_id.display_name))
            if pt.fruit_type == 'analysis' and pt.type != 'consu':
                raise ValidationError(_(
                    "Product '%s' has an Fruit Type 'Analysis', so "
                    "it must be configured as a consumable.")
                    % pt.display_name)
            if (
                    pt.fruit_type in ('service', 'extra_service', 'tax') and
                    pt.type != 'service'):
                raise ValidationError(_(
                    "Product '%s' has an Fruit Type 'Production Service', "
                    "'Extra Service' or 'Federation Tax', so it must be "
                    "configured as a Service.") % (
                        pt.display_name))


class ProductProduct(models.Model):
    _inherit = 'product.product'

    shrinkage_prodlot_id = fields.Many2one(
        'stock.production.lot', string='Shrinkage Production Lot',
        copy=False,
        help="Select the generic production lot that will be used for all "
        "moves of this fruit juice product to the shrinkage tank.")

    # DUPLICATED in product template
    @api.onchange('fruit_type')
    def fruit_type_change(self):
        liter_uom = self.env.ref('uom.product_uom_litre')
        if self.fruit_type == 'juice':
            if self.uom_id != liter_uom:
                self.uom_id = liter_uom
                self.uom_po_id = liter_uom
            self.tracking = 'lot'
        elif self.fruit_type == 'bottle_full':
            self.tracking = 'lot'
        if self.fruit_type in ('service', 'extra_service'):
            self.type = 'service'
        elif self.fruit_type == 'analysis':
            self.type == 'consu'
        if not self.fruit_type:
            self.fruit_culture_type = False

    def fruit_create_merge_bom(self):
        mbo = self.env['mrp.bom']
        for product in self.filtered(lambda p: p.fruit_type == 'juice'):
            mbo.create({
                'product_id': product.id,
                'product_tmpl_id': product.product_tmpl_id.id,
                'product_uom_id': product.uom_id.id,
                'product_qty': 1,
                'ready_to_produce': 'all_available',
                'bom_line_ids': [(0, 0, {
                    'product_id': product.id,
                    'product_uom_id': product.uom_id.id,
                    'product_qty': 1,
                    })],
                })

    def juice_bottle_full_get_bom_and_juice_product(self):
        self.ensure_one()
        assert self.fruit_type == 'bottle_full'
        boms = self.env['mrp.bom'].search([
            ('product_tmpl_id', '=', self.product_tmpl_id.id),
            ('type', '=', 'normal'),
            ('product_uom_id', '=', self.uom_id.id),
            ])
        if not boms:
            raise UserError(_(
                "No bill of material for product '%s'.") % self.display_name)
        if len(boms) > 1:
            raise UserError(_(
                "There are several bill of materials for product '%s'. "
                "This scenario is not supported.") % self.display_name)
        bom = boms[0]
        juice_bom_lines = self.env['mrp.bom.line'].search([
            ('product_id.fruit_type', '=', 'juice'), ('bom_id', '=', bom.id)])
        if not juice_bom_lines:
            raise UserError(_(
                "The bill of material '%s' (ID %d) doesn't have any "
                "line with an juice product.") % (bom.display_name, bom.id))
        if len(juice_bom_lines) > 1:
            raise UserError(_(
                "The bill of material '%s' (ID %d) has several lines "
                "with an juice product. This scenario is not supported for "
                "the moment.") % (bom.display_name, bom.id))
        juice_bom_line = juice_bom_lines[0]
        liter_uom = self.env.ref('uom.product_uom_litre')
        if juice_bom_line.product_uom_id != liter_uom:
            raise UserError(_(
                "The component line with product '%s' of the "
                "bill of material '%s' (ID %d) should have "
                "liters as the unit of measure.") % (
                    juice_bom_line.product_id.display_name,
                    bom.display_name, bom.id))
        volume = juice_bom_line.product_qty
        prec = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        if float_compare(volume, 0, precision_digits=prec) <= 0:
            raise UserError(_(
                "The juice volume (%s) can't negative on bill of "
                "material '%s' (ID %d).") % (
                    volume, bom.display_name, bom.id))
        return (bom, juice_bom_lines[0].product_id, volume)

    def juice_bottle_full_pack_get_bottles(self):
        self.ensure_one()
        assert self.fruit_type == 'bottle_full_pack'
        boms = self.env['mrp.bom'].search([
            ('product_tmpl_id', '=', self.product_tmpl_id.id),
            ('type', '=', 'normal'),
            ('product_uom_id', '=', self.uom_id.id),
            ])
        if not boms:
            raise UserError(_(
                "No bill of material for product '%s'.") % self.display_name)
        if len(boms) > 1:
            raise UserError(_(
                "There are several bill of materials for product '%s'. "
                "This scenario is not supported.") % self.display_name)
        bom = boms[0]
        full_bottle_lines = self.env['mrp.bom.line'].search([
            ('product_id.fruit_type', '=', 'bottle_full'), ('bom_id', '=', bom.id)])
        if not full_bottle_lines:
            raise UserError(_(
                "The bill of material '%s' (ID %d) doesn't have any "
                "line with a full juice bottle.") % (bom.display_name, bom.id))
        res = {}
        for full_bottle_line in full_bottle_lines:
            if full_bottle_line.product_id in res:
                res[full_bottle_line.product_id] += full_bottle_line.product_qty
            else:
                res[full_bottle_line.product_id] = full_bottle_line.product_qty
        return res
