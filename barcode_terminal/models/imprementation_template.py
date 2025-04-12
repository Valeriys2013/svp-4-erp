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

from odoo import models, fields, api
from odoo.addons.base.models.ir_model import FIELD_TYPES


class ImplementationFieldMappingLine(models.Model):
    _name = "barcode_terminal.implementation_field_mapping.line"
    _description = "Implementation mapping line for child record (with product) field"
    mapping_scheme_id = fields.Many2one(
        "barcode_terminal.implementation_field_mapping",
        required=True, ondelete='cascade'
    )

    internal_field = fields.Selection([('barcode', 'Barcode'), ('barcode_name', 'Barcode name'),
                                       ('barcode_comment', 'Barcode comment'), ('quantity', 'Quantity'),
                                       ('user_id', 'Responsible'), ('create_date', 'Creation date'),
                                       ('product', 'Product'), ('image_1920', 'Image (1920)'), ('uom_id', 'UoM'),
                                       ('price_unit', 'Unit Price'), ('product_tmpl_id', 'Product template')],
                                       string="Internal Field")

    target_doc_line_model = fields.Char(related='mapping_scheme_id.target_doc_line_model')
    external_field_id = fields.Many2one('ir.model.fields', 'External field', required=False,
                                        # domain=model_field_domain,
                                        ondelete='cascade')
    external_field = fields.Char(related='external_field_id.name', string="External field Name")
    external_field_type = fields.Selection(related='external_field_id.ttype', selection=FIELD_TYPES, string='External Field Type', required=True)

    @api.model
    def _reference_models(self):
        models = self.env['ir.model'].search([])
        # print([(model.model, model.name) for model in models])
        return [(model.model, model.name) for model in models]
    default_reference = fields.Reference(selection=lambda self: self._reference_models())

    @api.depends("mapping_scheme_id")
    def _compute_external_field_variants(self):
        res = []

        target_doc_line_model = self.mapping_scheme_id.target_doc_line_model
        print("self.mapping_scheme_id ---",self.mapping_scheme_id)
        if not target_doc_line_model:
            return res
        mf = self.env[target_doc_line_model].fields_get(
            attributes=['name', 'string', 'readonly', 'required', 'relation', 'type'])
        # print('mf ', mf)
        for f_key in mf:
            attrs = mf[f_key]
            res.append((f_key, attrs['string']))
        return res;


class ImplementationFieldMappingParentDocLine(models.Model):
    _name = "barcode_terminal.implementation_field_mapping.parent_doc_line"
    _description = "Implementation mapping line for parent doc field"
    mapping_scheme_id = fields.Many2one(
        "barcode_terminal.implementation_field_mapping",
        required=True, ondelete='cascade'
    )

    internal_field = fields.Selection([('user_id', 'Responsible'), ('create_date', 'Creation date'),
                                       ('name', 'Barcode Collection Name'), ('collection_comment', 'Barcode Collection Comment')],
                                       string="Internal Field")

    target_document_model = fields.Char(related='mapping_scheme_id.target_document_model')
    external_field_id = fields.Many2one('ir.model.fields', 'External field', required=False,
                                     # domain=model_field_domain,
                                        ondelete ='cascade')
    external_field = fields.Char(related='external_field_id.name', string="External field name")
    external_field_type = fields.Selection(related='external_field_id.ttype', selection=FIELD_TYPES, string='External Field Type', required=True)

    @api.model
    def _reference_models(self):
        models = self.env['ir.model'].search([])
        # # print([(model.model, model.name) for model in models])
        return [(model.model, model.name) for model in models]

    default_reference = fields.Reference(selection=lambda self: self._reference_models())

    def reference_models(self):
        print('_reference_models ', self._reference_models())


class ImplementationFieldMapping(models.Model):
    _name = "barcode_terminal.implementation_field_mapping"
    _description = "Implementation field mapping"

    active = fields.Boolean("Active?", default=True)
    allow_forced_creation = fields.Text("Allow Forced Creation?", related='param_ref_allow_forced.value')
    forced_creation = fields.Boolean("Forced creation?", default=False)
    name = fields.Char("Template name")
    target_document_model_id = fields.Many2one('ir.model', 'Target document model')
    target_document_model = fields.Char('Target document model',  related='target_document_model_id.model')
    document_lines_field_id = fields.Many2one('ir.model.fields', 'Target document multiline field', )
    document_lines_field_name = fields.Char('Target document multiline field name', related='document_lines_field_id.name', )
    target_doc_line_model = fields.Char('Target document line type', related='document_lines_field_id.relation',)
    autocreate_identifier = fields.Char()

    doc_attrib_ids = fields.One2many(
        "barcode_terminal.implementation_field_mapping.parent_doc_line",
        "mapping_scheme_id",
        string="Field implementation mapping for parent doc",
    )

    prod_line_ids = fields.One2many(
        "barcode_terminal.implementation_field_mapping.line",
        "mapping_scheme_id",
        string="Field implementation mapping for lines",
    )

    def print_models(self):
        print("self.target_document_model ", self.target_document_model)
        # dic = dict(self.target_models_data)
        # print(dic)

    def sticky_notification(self, message):
        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Warning',
                'message': message,
                'sticky': True,
            }
        }
        return notification

    @api.model
    def ensure_find_allow_forced_creation(self):
        cnt = self.env['ir.config_parameter'].sudo().search_count([('key', '=', 'barcode_terminal.allow_forced_creation')], limit=1)
        if cnt == 0:
            self.env['ir.config_parameter'].set_param('barcode_terminal.allow_forced_creation', '0')
        params = self.env['ir.config_parameter'].sudo().search([('key', '=', 'barcode_terminal.allow_forced_creation')], limit=1)
        # print("params-", params)
        # print("value-", params.value)
        return params.ids[0]

    param_ref_allow_forced = fields.Many2one('ir.config_parameter',"Config record reference")

    @api.model
    def create(self, vals):
        vals['param_ref_allow_forced'] = self.ensure_find_allow_forced_creation()
        return super(ImplementationFieldMapping, self).create(vals)

    @api.model
    def find_new_template(self, timestamp):
        records_cnt = self.search_count([('timestamp', '=', timestamp)], limit=1)
        res = {'records_cnt': records_cnt, }
        return res

    timestamp = fields.Char('timestamp')


