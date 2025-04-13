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


class Implementation(models.Model):
    _name = 'barcode_terminal.implementation'
    _description = 'Implementation into real document'
    name = fields.Char()
    source_collection_id = fields.Many2one("barcode_terminal.barcode_collection", string="Source collection")
    target_type_id = fields.Many2one("barcode_terminal.implementation_field_mapping",string="Implementation template")
    # document_model_id = fields.Char('Target document type', store=True)
    target_document_model = fields.Char('Target document model', store=True, related='target_type_id.target_document_model')
    target_document_model_name = fields.Char('Target document model', related='target_type_id.target_document_model_id.display_name')
    # document_model_id = fields.Many2one('ir.model', related='target_type_id.document_model_id')
    target_doc_line_model = fields.Char('Target lines model', store=True, related='target_type_id.target_doc_line_model')
    document_lines_field_name = fields.Char('Target lines field', store=True, related='target_type_id.document_lines_field_name')
    # doc_model = fields.Date(string="Document type")
    wizard_start = fields.Datetime(string="Wizard start time")


    @api.model
    def _reference_models(self):
        # models = self.env['ir.model'].search([('model', '=', self.document_model_id)])
        # models = self.env['ir.model'].search([('model', '=', 'sale.order')])
        target_document_model = self.target_document_model
        for rec in self:
            target_document_model = rec.target_document_model;
        # print("self.doc_model ", self.doc_model)
        # print("document_model_id ", document_model_id)
        if target_document_model:
            # models = self.env['ir.model'].search([('model', '=', 'sale.order')])
            models = self.env['ir.model'].search([('model', '=', self.target_document_model)])
            # print("models ", models)
        else:
            # models = self.env['ir.model'].search([('model', '=', 'sale.order')])
            models = self.env['ir.model'].search([])
        # print([(model.model, model.name) for model in models])
        return [(model.model, model.name) for model in models]

    # document_reference = fields.Reference(selection='_reference_models')
    document_reference = fields.Reference(selection=lambda self: self._reference_models(), required=False)
    result_doc_name = fields.Char('Result')
    # result_doc_name = fields.Char('Result', compute="compute_result_name", store=False)

    # @api.depends('document_reference')
    # def compute_result_name(self):
    #     if self.document_reference:
    #         for rec in self:
    #             rec.result_doc_name = self.document_reference.name
    #     else:
    #         for rec in self:
    #             rec.result_doc_name = ""

    # @api.onchange('target_type_id')
    # def _onchange_target_type_id(self):
    #     # self.document_reference.__setattr__('selectors', '_reference_models')
    #     self.document_reference.__setattr__('select', self._reference_models())

    def print_document_model_id(self):
        print("self.target_document_model ", self.target_document_model)
        # dic = dict(self.target_models_data)
        # print(dic)

    def get_user_last_sale_attributes(self):
        last_sale = self.env['sale.order'].search(
                    [ ('user_id', '=', self.env.uid)],  order="create_date desc", limit=1)
        if last_sale:
            customer = last_sale.partner_id.id
            pricelist = customer.property_product_pricelist
            return {'customer' : customer, 'pricelist' : pricelist, }
        else: return False
    #
    # def generate_target_doc(self):
    #     mf = self.env[self.document_model_id].fields_get( attributes=['name'])
    #     field_List = list(mf.keys())
    #     default_vals = self.env[self.document_model_id].default_get(field_List)
    #
    #     print('default_vals :::::::::::', default_vals)
    #     parent_doc_line_vals = []
    #     # parent_doc_id = self.env[self.document_model_id].name_create(self.source_collection_id.name)
    #     self.print_document_model_id()
    #
    #     for product_line in self.source_collection_id.line_ids:
    #         if not product_line['product']:
    #             continue
    #         new_line = {}
    #         for mapping_row in self.target_type_id.prod_line_ids:
    #             if mapping_row.external_field and mapping_row.internal_field:
    #                 if mapping_row.external_field_type == 'many2one':
    #                     new_line[mapping_row.external_field] = product_line[mapping_row.internal_field].id
    #                 else:
    #                     new_line[mapping_row.external_field] = product_line[mapping_row.internal_field]
    #         # parent_doc_line_id = self.env[self.target_doc_line_model].create([parent_doc_line_vals])
    #         # new_line['product_id'] = product_line['product'].id
    #         parent_doc_line_vals.append(fields.Command.create(new_line))
    #         # parent_doc_line_vals.append((0, 0, new_line))
    #         # parent_doc_line_vals.append(new_line)
    #     print("parent_doc_line_vals>>>>", parent_doc_line_vals)
    #     print("document_lines_field_name>>>>", self.document_lines_field_name)
    #     # self.document_reference = '% s,% s' % (self.target_doc_line_model, parent_doc_id)
    #
    #     ctx = self.env.context.copy()
    #
    #     for field_nam in default_vals:
    #         ctx.update({
    #             'default_' + field_nam: default_vals[field_nam],
    #         })
    #
    #     ctx.update({
    #         'default_' + self.document_lines_field_name: parent_doc_line_vals,
    #         # 'default_partner_id': self.partner_id.id,
    #     })
    #     ctx.update({
    #         'default_active_ids': self.source_collection_id.ext_id,
    #         # 'default_partner_id': self.partner_id.id,
    #     })
    #     # print("'default_' + self.document_lines_field_name ", 'default_' + self.document_lines_field_name)
    #     print('ctx0', ctx)
    #     # res_id = {
    #     return {
    #         'name': ('Payments'),
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'res_model': self.document_model_id,
    #         'view_id': False,
    #         'type': 'ir.actions.act_window',
    #         'target': 'new',
    #         'context': ctx
    #         # 'context': {
    #         #     # 'default_order_line' : (0, 0, [{'product_uom_qty' : 1649}]),
    #         #     'default_' + self.document_lines_field_name: parent_doc_line_vals,
    #         #     # 'default_' + self.document_lines_field_name: self.env[self.target_doc_line_model].new(parent_doc_line_vals),
    #         #     # 'default_name': 'default_name',
    #         # },
    #     }
    #     # print('res_id ',res_id)

    def open_target_reference(self):
        res_model = self.target_document_model
        document_reference = self.document_reference
        # print('document_reference.name', document_reference.name)
        return {'type': 'ir.actions.act_window',
                'name': 'Open target reference',
                'res_model': res_model,
                'res_id': document_reference.id,
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'current',
                }

