# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2025 Valery Svetlitsky
#    Author: Valery Svetlitsky
#    License: GNU Affero General Public License (AGPL) version 3
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3)
#    <http://www.gnu.org/licenses/> for more details.
#
##############################################################################
{
    "name": "Barcode terminal",
    "summary": """
        Leverage of mobile barcode recognition facility""",
    "description": """
        This application is ment for collection of barcode data
        representing SKUs , using mobile application SVP Barcode
        Collector (BCC). This provides cheap and handy way to 
        simplify different kinds of tidious operations , as inventory,
        stock taking, etc. , including the ability to add images of
        goods by means of mobile camera 
    """,
    "author": "Valery Svetlitsky",
    "website": "https://sites.google.com/view/svp-barcodecollector/home",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "category": "Inventory",
    "version": "0.9",
    # any module necessary for this one to work correctly
    # "depends": ["base", "product", "base_import", "mail", "contacts"],
    "depends": ["base", "product", "base_import", "sale", "mail", "contacts", "sale_management", "stock"],

    # always loaded
    "data": [
        "security/ir.model.access.csv",
        "views/implementation_views.xml",
        "views/views.xml",
        "views/collection_alias_view.xml",
        "views/implementation_tuning_views.xml",
        "views/templates.xml",
        "views/res_config_settings_views.xml",
        "wizard/import_zip_dialog_view.xml",
        "wizard/implementation_wizard.xml",
        "wizard/implementation_template_wizard.xml",
        "data/mail_template.xml",
    ],
    'assets': {
        'web.assets_backend': [
            'barcode_terminal/static/src/js/barcode_collection_formcontroller.js',
            'barcode_terminal/static/src/js/barcode_collection_formcontroller.xml',
            'barcode_terminal/static/src/js/my_list_view_controller.js',
            'barcode_terminal/static/src/js/my_list_view_controller.xml',
        ],
    },
    # only loaded in demonstration mode
    "demo": [
        "demo/demo.xml",
    ],
    'images': [
        # 'static/description/main_screenshot.png'
        # 'static/description/Fig1.png',
        # 'static/description/Fig2.png',
        # 'static/description/Fig3.png',
        # 'static/description/Fig4.png',
        # 'static/description/Fig5.png',
        # 'static/description/Fig6.png',
        # 'static/description/Fig7.png',
        # 'static/description/Fig8.png',
        # 'static/description/Fig9.png',
        # 'static/description/Fig10.png',
        # 'static/description/Fig11.png',
        # 'static/description/icon.png',
        'static/description/banner.png'
    ],

    "application": True,
    'license': 'AGPL-3',
}
