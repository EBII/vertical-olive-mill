# Copyright 2018 Barroux Abbey (https://www.barroux.org/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class FruitVariant(models.Model):
    _name = 'fruit.variant'
    _description = 'Fruit Variant'
    _order = 'sequence'

    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer()
    active = fields.Boolean(default=True)
    # fruit_culture_type = fields.Selection([
    #    ('regular', 'Regular'),
    #    ('organic', 'Organic'),
    #    ('conversion', 'Conversion'),
    #    ], string='Culture Type')

    _sql_constraints = [(
        'name_unique',
        'unique(name)',
        'This fruit variant already exists.')]
