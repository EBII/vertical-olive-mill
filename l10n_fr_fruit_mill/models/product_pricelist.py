# Copyright 2019 Barroux Abbey (https://www.barroux.org/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    fruit_juice_distributor = fields.Boolean(
        string='Fruit Juice Distributor', help="Field used for AgriMer reports")
