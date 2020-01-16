# Copyright 2019 Barroux Abbey (https://www.barroux.org/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.tools import float_is_zero


class FruitPartnerWarningPrint(models.TransientModel):
    _name = 'fruit.partner.warning.print'
    _description = 'Wizard to print list of fruit farmer warnings'

    season_id = fields.Many2one(
        'fruit.season', string='Season', required=True,
        default=lambda self: self.env.user.company_id.current_season_id.id)

    def report_get_lines(self):
        self.ensure_one()
        res = []
        prec = self.env['decimal.precision'].precision_get('Fruit Weight')
        partners = self.env['res.partner'].with_context(season_id=self.season_id.id).search(
            [('parent_id', '=', False), ('fruit_farmer', '=', True)])
        for p in partners:
            fruit_qty = p.fruit_qty_current_season
            if (
                    not float_is_zero(fruit_qty, precision_digits=prec) and
                    (p.fruit_cultivation_form_ko or
                     p.fruit_parcel_ko or
                     p.fruit_organic_certif_ko or
                     p.fruit_invoicing_ko)):
                res.append({
                    'name': p.name_title,
                    'fruit_qty': int(round(fruit_qty, 0)),
                    'fruit_qty_triturated': int(round(p.fruit_qty_triturated_current_season, 0)),
                    'cultivation_form': p.fruit_cultivation_form_ko and 'X' or '',
                    'parcel': p.fruit_parcel_ko and 'X' or '',
                    'organic_certif': p.fruit_organic_certif_ko and 'X' or '',
                    'invoicing': p.fruit_invoicing_ko and 'X' or '',
                    })
        return res

    def run(self):
        self.ensure_one()
        action = self.env['report'].get_action(self, 'fruit.partner.warning')
        return action
