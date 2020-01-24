# Copyright 2019 Barroux Abbey (https://www.barroux.org/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'French localization for fruit mill',
    'version': '12.0.1.0.0',
    'category': 'Manufacturing',
    'license': 'AGPL-3',
    'summary': 'AgriMer reports on fruit mill',
    'author': 'Akretion,Barroux Abbey',
    'website': 'https://github.com/akretion/vertical-fruit-mill',
    'depends': [
        'fruit_mill',
        'date_range',
        ],
    'data': [
        'security/fruit_security.xml',
        'security/ir.model.access.csv',
        'views/fruit_agrimer_report.xml',
        'views/product.xml',
        'views/product_pricelist.xml',
    ],
    'installable': True,
    'application': True,
}
