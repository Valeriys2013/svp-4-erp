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

from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    # _description = 'Description'
    allow_forced_creation = fields.Boolean(string="Allow Forced Creation", default=False,
                                           # config_parameter='barcode_terminal.allow_forced_creation',
                               help="Allow use templates with for forced implementation type"
                                    "(creating documents at once not showing form view)" )

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        param = '0'
        if self.allow_forced_creation:
            param = '1'
        # print('set barcode_terminal.allow_forced_creation --- ', param)
        self.env['ir.config_parameter'].set_param(
            'barcode_terminal.allow_forced_creation', param)

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        # print('get barcode_terminal.allow_forced_creation --- ', params.get_param('barcode_terminal.allow_forced_creation'))
        params_get_param = params.get_param('barcode_terminal.allow_forced_creation')
        bool_param = False
        if params_get_param != '0':
            bool_param = True
        res.update(
            allow_forced_creation=bool_param
        )
        return res
