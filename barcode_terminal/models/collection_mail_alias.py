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

from email.policy import default

from odoo import fields, models, api
from ast import literal_eval
import json



class CollectionMailAlias(models.Model):
    _name = 'barcode_terminal.collection_mail_alias'
    _description = 'Barcode collection EMail alias'
    _inherit = ['mail.thread', 'mail.alias.mixin']

    name = fields.Char(tracking=True)
    subject_prefix = fields.Char(required=False, default="barcodecollector data")
    attachment_prefix = fields.Char(required=False)
    # state = fields.Selection([('draft', 'New'), ('confirmed', 'Confirmed')], tracking=True)
    # collection_ids = fields.One2many('barcode_terminal.barcode_collection', 'mail_alias_id', 'Collections')
    alias_id = fields.Many2one('mail.alias', string='Alias', ondelete="restrict", required=True)

    # def _get_alias_model_name(self, vals):
    #     """ Specify the model that will get created when the alias receives a message """
    #     return 'barcode_terminal.barcode_collection'

    # def _get_alias_values(self):
    #     """ Specify some default values that will be set in the alias at its creation """
    #     values = super(CollectionMailAlias, self)._get_alias_values()
    #     # values = {}
    #     # alias_defaults holds a dictionary that will be written
    #     # to all records created by this alias
    #     #
    #     # in this case, we want all expense records sent to a trip alias
    #     # to be linked to the corresponding business trip
    #     # values['alias_defaults'] = {'trip_id': self.id}
    #     # we only want followers of the trip to be able to post expenses
    #     # by default
    #     values['alias_contact'] = 'everyone'
    #     # values['subject_prefix'] = self.subject_prefix
    #     # values['attachment_prefix'] = self.attachment_prefix
    #     values['alias_defaults'] = str({'subject_prefix': self.subject_prefix,'attachment_prefix': self.attachment_prefix})
    #     print("values:  ", values)
    #     return values

    def _alias_get_creation_values(self):
        values = super(CollectionMailAlias, self)._alias_get_creation_values()
        values['alias_model_id'] = self.env['ir.model']._get('barcode_terminal.barcode_collection').id
        if self.id:
            values['alias_defaults'] = defaults = literal_eval(self.alias_defaults or "{}")
            defaults['subject_prefix'] = self.subject_prefix
            defaults['attachment_prefix'] = self.attachment_prefix
        return values

    # @api.onchange("subject_prefix", "attachment_prefix")
    # def _onchange_prefixes(self):
    #     self.alias_defaults = str({'subject_prefix': self.subject_prefix,'attachment_prefix': self.attachment_prefix})

    def write(self, vals):
        res =  super(CollectionMailAlias, self).write(vals)
        for record in self:
            alias_defaults = str({'subject_prefix': record['subject_prefix'], 'attachment_prefix': record['attachment_prefix']})
            vals.update({'alias_defaults': alias_defaults})
        return super(CollectionMailAlias, self).write(vals)
