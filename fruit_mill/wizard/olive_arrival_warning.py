# Copyright 2018-2019 Barroux Abbey (https://www.barroux.org/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class FruitArrivalWarning(models.TransientModel):
    _name = 'fruit.arrival.warning'
    _description = 'Fruit arrivals warning'

    arrival_id = fields.Many2one('fruit.arrival', required=True)
    show_validation_button = fields.Boolean()
    count = fields.Integer(readonly=True)
    msg = fields.Text(readonly=True)

    def validate(self):
        self.ensure_one()
        assert self.show_validation_button
        self.arrival_id.with_context(fruit_no_warning=True).validate()
        return
