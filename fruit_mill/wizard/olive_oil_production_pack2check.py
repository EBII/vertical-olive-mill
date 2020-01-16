# Copyright 2018 Barroux Abbey (https://www.barroux.org/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class FruitJuiceProductionPack2Check(models.TransientModel):
    _name = 'fruit.juice.production.pack2check'
    _description = 'Fruit Juice Production Pack2check'

    production_id = fields.Many2one(
        'fruit.juice.production', string='Fruit Juice Production', required=True)
    palox_id = fields.Many2one(
        related='production_id.palox_id', readonly=True)
    juice_product_id = fields.Many2one(
        related='production_id.juice_product_id', readonly=True)
    todo_arrival_line_ids = fields.Many2many(
        'fruit.arrival.line', string='Arrival Lines Left to Process')
    arrival_line_id = fields.Many2one(
        'fruit.arrival.line', string='Production Line',
        readonly=False, required=True)
    line_juice_ratio = fields.Float(
        related='arrival_line_id.juice_ratio', readonly=True)
    line_withdrawal_juice_qty = fields.Float(
        related='arrival_line_id.withdrawal_juice_qty', readonly=True)
    line_withdrawal_juice_qty_kg = fields.Float(
        related='arrival_line_id.withdrawal_juice_qty_kg', readonly=True)
    extra_ids = fields.One2many(
        related='arrival_line_id.extra_ids', readonly=False)

    @api.model
    def default_get(self, fields_list):
        res = super(FruitJuiceProductionPack2Check, self).default_get(
            fields_list)
        prod = self.env['fruit.juice.production'].browse(
            res.get('production_id'))
        line_ids = [
            line.id for line in prod.line_ids
            if line.juice_destination in ('withdrawal', 'mix')]
        if line_ids:
            res['arrival_line_id'] = line_ids.pop(0)
        if line_ids:
            res['todo_arrival_line_ids'] = [(6, 0, line_ids)]
        return res

    def validate(self):
        self.ensure_one()
        prod = self.production_id
        if self.todo_arrival_line_ids:
            new_line_id = self.todo_arrival_line_ids[0].id
            self.write({
                'arrival_line_id': new_line_id,
                'todo_arrival_line_ids': [(3, new_line_id)],
                })
            action = self.env['ir.actions.act_window'].for_xml_id(
                'fruit_mill', 'fruit_juice_production_pack2check_action')
            action['res_id'] = self.id
            return action
        else:
            prod.pack2check()
            return True
