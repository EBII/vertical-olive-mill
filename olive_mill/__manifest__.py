# Copyright 2018 Barroux Abbey (https://www.barroux.org/)
# @author: Alexis de Lattre <alexis.delattre@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Olive Mill',
    'version': '12.0.1.0.0',
    'category': 'Manufacturing',
    'license': 'AGPL-3',
    'summary': 'Manage an olive mill',
    'author': 'Akretion,Barroux Abbey',
    'website': 'https://github.com/akretion/vertical-olive-mill',
    'depends': [
        'mrp',
        'account',
        'product_expiry_simple',
        'base_location',
        # 'stock_no_negative',  # ??
        #'stock_pack_operation_auto_fill',
        'report_py3o',
        'base_usability',  # for reports
        'onchange_helper',
        'base_view_inheritance_extension',
        ],
    'data': [
        'security/olive_security.xml',
        'security/ir.model.access.csv',
        'data/decimal_precision.xml',
        'data/sequence.xml',
        'data/organic_certifying_entity.xml',
        #'data/cron.xml',
        'views/menu.xml',
        'wizard/olive_palox_case_lend_view.xml',
        'wizard/olive_palox_generate_production_view.xml',
        'wizard/olive_withdrawal_view.xml',
        'wizard/olive_invoice_create_view.xml',
        'wizard/olive_oil_production_ratio2force_view.xml',
        'wizard/olive_oil_production_force_ratio_view.xml',
        'wizard/olive_oil_production_pack2check_view.xml',
        'wizard/olive_oil_tank_transfer.xml',
        'wizard/olive_arrival_warning_view.xml',
        'wizard/olive_oil_production_compensation_view.xml',
        'wizard/olive_oil_production_product_swap_view.xml',
        'wizard/olive_oil_tank_merge_view.xml',
        'wizard/olive_oil_bottling_view.xml',
        'wizard/olive_oil_picking_view.xml',
        'wizard/olive_appointment_print_view.xml',
        'wizard/olive_oil_production_day_print_view.xml',
        'wizard/olive_partner_warning_print_view.xml',
        'views/olive_config_settings.xml',
        'views/stock_location.xml',
        'views/stock_warehouse.xml',
        'views/stock_picking.xml',
        'views/olive_variant.xml',
        'views/olive_ochard.xml',
        'views/olive_parcel.xml',
        'views/olive_palox.xml',
        'views/olive_season.xml',
        'views/olive_lended_case.xml',
        'views/olive_cultivation.xml',
        'views/olive_treatment.xml',
        'views/olive_arrival.xml',
        'report/report.xml',
        'views/olive_oil_production.xml',
        'views/partner_organic_certification.xml',
        'views/olive_appointment.xml',
        'views/olive_preseason_poll.xml',
        'views/olive_sale_pricelist.xml',
        'views/organic_certifying_entity.xml',
        #'views/partner.xml',
        'views/users.xml',
        'views/product.xml',
        'views/stock_production_lot.xml',
        'views/olive_oil_analysis.xml',
    ],
    'demo': [
        'demo/product.xml',
        'demo/olive_variant.xml',
        'demo/company.xml',
        'demo/olive_sale_pricelist.xml',
        'demo/partner.xml',
        'demo/stock_production_lot.xml',
        'demo/stock_location.xml',
        'demo/stock_warehouse.xml',
        'demo/olive_ochard.xml',
        'demo/olive_season.xml',
        'demo/olive_treatment.xml',
        'demo/olive_parcel.xml',
        'demo/olive_palox.xml',
        ],
    'installable': True,
    'application': True,
}
