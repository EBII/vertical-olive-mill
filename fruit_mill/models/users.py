# Copyright 2018 Barroux Abbey (https://www.barroux.org/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    fruit_operator = fields.Boolean(string='Fruit Mill Operator')

    def _default_fruit_mill_wh(self):
        self.ensure_one()
        wh = self.env['stock.warehouse'].search([
            ('company_id', '=', self.company_id.id),
            ('fruit_mill', '=', True)],
            limit=1)
        return wh
