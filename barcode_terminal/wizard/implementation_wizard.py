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

import datetime
from datetime import timedelta

from odoo import fields, models, api
from odoo.tools.translate import _


class ImplementWizard(models.TransientModel):
    _name = 'barcode_terminal.implementation_wizard'
    _description = 'Wizard for implementation to primary records'

    name = fields.Char()
    source_collection_id = fields.Many2one("barcode_terminal.barcode_collection", string="Source collection")
    target_type_id = fields.Many2one("barcode_terminal.implementation_field_mapping", string="Implementation template",
    domain = "['|', ('allow_forced_creation', '=', '1'), ('forced_creation', '=', False)]"
    )
    target_document_model = fields.Char('Target document model', store=True, related='target_type_id.target_document_model')
    target_doc_line_model = fields.Char('Target lines model', store=True,
                                         related='target_type_id.target_doc_line_model')
    document_lines_field_name = fields.Char('Target lines field', store=True,
                                            related='target_type_id.document_lines_field_name')

    def get_user_last_sale_attributes(self):
        last_sale = self.env['sale.order'].search(
                    [ ('user_id', '=', self.env.uid)],  order="create_date desc", limit=1)
        if last_sale:
            customer = last_sale.partner_id
            fiscal_position_id = last_sale.fiscal_position_id
            pricelist = customer.property_product_pricelist
            return {'customer' : customer.id, 'pricelist' : pricelist, 'fiscal_position_id' : fiscal_position_id, }
        else: return False
    
    def _get_some_picking_defaults(self):
        picking_picking_type_id = self.env.ref('stock.picking_type_internal')
        picking_company_id = self.env.company.id
        picking_partner_id = self.env.company.partner_id.id
        if picking_picking_type_id:
            if picking_picking_type_id.default_location_src_id:
                location_id = picking_picking_type_id.default_location_src_id.id
            elif picking_partner_id:
                location_id = picking_partner_id.property_stock_supplier.id
            else:
                _customerloc, location_id = self.env['stock.warehouse']._get_partner_locations()

            if picking_picking_type_id.default_location_dest_id:
                location_dest_id = picking_picking_type_id.default_location_dest_id.id
            elif picking_partner_id:
                location_dest_id = picking_partner_id.property_stock_customer.id
            else:
                location_dest_id, _supplierloc = self.env['stock.warehouse']._get_partner_locations()

        # print('_get_some_picking_defaults.location_dest_id-----', location_dest_id)
        return {'location_id' : location_id, 'location_dest_id' : location_dest_id,
                    'picking_company_id' : picking_company_id, 'picking_picking_type_id' : picking_picking_type_id.id,
                    'picking_partner_id' : picking_partner_id }
    def _get_product_purchase_description(self, product_lang):
        self.ensure_one()
        name = product_lang.display_name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase

        return name


    def generate_implementation(self):
        recognized_product_cnt = 0
        for product_line in self.source_collection_id.line_ids:
            if product_line['product']:
                recognized_product_cnt = recognized_product_cnt +1
        if recognized_product_cnt == 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _("Nothing to implement"),
                    'type': 'warning',
                    'message': _("Implementation is for PRODUCTS, that should be recognized for barcodes and present in "
                                 "collection table. Currently -0- recognized. "
                                 "Please use toolbar buttons to recognize products (or generate new) "
                                 "before launching this wizard"),
                    'sticky': True,
                },
            }

        if self.target_type_id['forced_creation']:
            wizard_start = datetime.datetime.now() + timedelta(seconds=-1)
            new_doc_id =  self.create_implementation()

            self.env["barcode_terminal.implementation"].create(
                [{
                    "source_collection_id": self.env.context['default_source_collection_id'],
                    "target_type_id": self.target_type_id.id,
                    "target_document_model": self.target_document_model,
                    "target_doc_line_model": self.target_doc_line_model,
                    "document_lines_field_name": self.document_lines_field_name,
                    "wizard_start": wizard_start,
                    # "document_reference": new_doc_id,
                    # "result_doc_name": new_doc_id.display_name,
                }]
            )
            return True

        mf_doc = self.env[self.target_document_model].fields_get( attributes=['name', 'type'])
        field_List = list(mf_doc.keys())
        default_vals = self.env[self.target_document_model].default_get(field_List)
        # print('default_vals :::::::::::', default_vals)
        mf = self.env[self.target_doc_line_model].fields_get(attributes=['name', 'type'])
        field_List = list(mf.keys())
        default_line_vals = self.env[self.target_doc_line_model].default_get(field_List)
        # print('default_line_vals :::::::::::', default_line_vals)
        ctx = self.env.context.copy()
        # Not sure - may be this is redundant and defaults will be set by platform itself
        for field_nam in default_vals:
            def_field_nam = 'default_' + field_nam
            ctx[def_field_nam] = default_vals[field_nam]

        if self.target_document_model == 'stock.picking':
            ctx['default_origin'] = 'Barcode collection (' + self.source_collection_id['name'] + ')'

        if self.target_document_model == 'purchase.order':
            ctx['default_origin'] = 'Barcode collection (' + self.source_collection_id['name'] + ')'

        if self.target_document_model == 'sale.order':
            ctx['default_origin'] = 'Barcode collection (' + self.source_collection_id['name'] + ')'
            ctx['default_company_id'] = self.env.company.id
            ctx['default_has_active_pricelist'] = False
            ctx['default_state'] = '' #just to workaround issue with '_onchange_company_id_warning'
            # method in "sale.order" which hang  the program into endless loop
            last_sale_att = self.get_user_last_sale_attributes()
            if last_sale_att:
                ctx['default_partner_id'] = last_sale_att['customer']
                ctx['default_pricelist_id'] = last_sale_att['pricelist']
                ctx['default_fiscal_position_id'] = last_sale_att['fiscal_position_id']

        internal_transfer_defaults = {}
        # print('self.document_model_id-----', self.document_model_id)

        parent_doc_line_vals = []
        # self.print_document_model_id()
        for mapping_row in self.target_type_id.doc_attrib_ids:
            if mapping_row.external_field and mapping_row.internal_field:
                def_attrib_name = 'default_' + mapping_row.external_field
                if mapping_row.external_field_type == 'many2one':
                    ctx[def_attrib_name] = self.source_collection_id[mapping_row.internal_field].id
                else:
                    ctx[def_attrib_name] = self.source_collection_id[mapping_row.internal_field]
            elif mapping_row.external_field and mapping_row.default_reference:
                def_attrib_name = 'default_' + mapping_row.external_field
                ctx[def_attrib_name] = mapping_row.default_reference.id

        if self.target_document_model == 'stock.picking':
            # print('internal_transfer_defaults>>>>>>>')
            internal_transfer_defaults = self._get_some_picking_defaults()
            # print('internal_transfer_defaults-----', internal_transfer_defaults)
            ctx['default_company_id'] = self.env.company.id
            ctx['default_partner_id'] = self.env.company.partner_id.id
            ctx['default_picking_type_id'] = self.env.ref('stock.picking_type_internal').id
            ctx['default_location_id'] = internal_transfer_defaults['location_id']
            ctx['default_location_dest_id'] = internal_transfer_defaults['location_dest_id']
            # ctx['default_immediate_transfer'] = True
            # ctx.pop('default_immediate_transfer', None)

        if self.target_document_model == 'product.pricelist':
            ctx['default_company_id'] = self.env.company.id

#################################

        for product_line in self.source_collection_id.line_ids:
            if not product_line['product']:
                continue
            new_line = {}
            # Not sure - may be this is redundant and defaults will be set by platform itself
            new_line.update(default_line_vals)
            for mapping_row in self.target_type_id.prod_line_ids:
                if mapping_row.external_field and mapping_row.internal_field:
                    if mapping_row.external_field_type == 'many2one':
                        new_line[mapping_row.external_field] = product_line[mapping_row.internal_field].id
                    else:
                        new_line[mapping_row.external_field] = product_line[mapping_row.internal_field]
                elif mapping_row.external_field and mapping_row.default_reference:
                    new_line[mapping_row.external_field] = mapping_row.default_reference.id

            if (len(new_line) == 0):
                continue

            if self.target_document_model == 'stock.picking':
                # internal_transfer_defaults = self._get_some_picking_defaults()
                new_line['company_id'] = self.env.company.id
                new_line['partner_id'] = self.env.company.partner_id.id
                new_line['picking_type_id'] = self.env.ref('stock.picking_type_internal').id
                new_line['location_id'] = internal_transfer_defaults['location_id']
                new_line['location_dest_id'] = internal_transfer_defaults['location_dest_id']

            if self.target_document_model == 'purchase.order':
                new_line['name'] = self._get_product_purchase_description(product_line['product'])

            if self.target_document_model == 'product.pricelist':
                # new_line['date_start'] = fields.Datetime.now()
                # new_line['applied_on'] = '1_product'
                new_line['applied_on'] = '0_product_variant'
                new_line['compute_price'] = 'fixed'
                new_line['company_id'] = self.env.company.id

            if self.target_document_model == 'sale.order':
                new_line['product_updatable'] = False

            parent_doc_line_vals.append(fields.Command.create(new_line))

        ctx.update({
            'default_' + self.document_lines_field_name: parent_doc_line_vals,
        })
        #print('ctx0', ctx)
        wizard_start = datetime.datetime.now()
        self.env["barcode_terminal.implementation"].create(
            [{
                "source_collection_id": self.env.context['default_source_collection_id'],
                "target_type_id": self.target_type_id.id,
                "target_document_model": self.target_document_model,
                "target_doc_line_model": self.target_doc_line_model,
                "document_lines_field_name": self.document_lines_field_name,
                "wizard_start": wizard_start,
                # "document_reference": , just has to be filled
            }]
        )

        return {
            'name': 'New Document (' + self.target_document_model + ")",
            "views": [[False, "form"]],
            # 'view_type': 'form',
            'view_mode': 'form',
            'res_model': self.target_document_model,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx
        }
        # print('res_id ',res_id)

    def create_implementation(self):
        mf_doc = self.env[self.target_document_model].fields_get( attributes=['name', 'type'])
        field_List = list(mf_doc.keys())
        default_vals = self.env[self.target_document_model].default_get(field_List)
        # print('default_vals :::::::::::', default_vals)
        mf = self.env[self.target_doc_line_model].fields_get(attributes=['name', 'type'])
        field_List = list(mf.keys())
        default_line_vals = self.env[self.target_doc_line_model].default_get(field_List)

        # print('default_line_vals :::::::::::', default_line_vals)
        # ctx = self.env.context.copy()
        # Not sure - may be this is redundant and defaults will be set by platform itself
        dic = {}
        for field_nam in default_vals:
            def_field_nam = field_nam
            dic[def_field_nam] = default_vals[field_nam]

        if self.target_document_model == 'sale.order':
            dic['company_id'] = self.env.company.id
            last_sale_att = self.get_user_last_sale_attributes()
            if last_sale_att:
                dic['partner_id'] = last_sale_att['customer']
                dic['pricelist_id'] = last_sale_att['pricelist']
        internal_transfer_defaults = {}
        # print('self.document_model_id-----', self.document_model_id)
        parent_doc_line_vals = []
        # self.print_document_model_id()
        for mapping_row in self.target_type_id.doc_attrib_ids:
            if mapping_row.external_field and mapping_row.internal_field:
                def_attrib_name = '' + mapping_row.external_field
                if mapping_row.external_field_type == 'many2one':
                    dic[def_attrib_name] = self.source_collection_id[mapping_row.internal_field].id
                else:
                    dic[def_attrib_name] = self.source_collection_id[mapping_row.internal_field]
            elif mapping_row.external_field and mapping_row.default_reference:
                def_attrib_name = mapping_row.external_field
                dic[def_attrib_name] = mapping_row.default_reference.id

        if self.target_document_model == 'stock.picking':
            # print('internal_transfer_defaults>>>>>>>')
            internal_transfer_defaults = self._get_some_picking_defaults()
            # print('internal_transfer_defaults-----', internal_transfer_defaults)
            dic['company_id'] = self.env.company.id
            dic['partner_id'] = self.env.company.partner_id.id
            dic['picking_type_id'] = self.env.ref('stock.picking_type_internal').id
            dic['location_id'] = internal_transfer_defaults['location_id']
            dic['location_dest_id'] = internal_transfer_defaults['location_dest_id']

        if self.target_document_model == 'product.pricelist':
            dic['company_id'] = self.env.company.id

        print("self.target_document_model>>>>", self.target_document_model)
        document = self.env[self.target_document_model].create(dic)
        document.write({self.document_lines_field_name: [(5, 0, 0)]})

        #################################

        for product_line in self.source_collection_id.line_ids:
            if not product_line['product']:
                continue
            new_line = {}
            # Not sure - may be this is redundant and defaults will be set by platform itself
            new_line.update(default_line_vals)
            for mapping_row in self.target_type_id.prod_line_ids:

                if mapping_row.external_field and mapping_row.internal_field:
                    if mapping_row.external_field_type == 'many2one':
                        new_line[mapping_row.external_field] = product_line[mapping_row.internal_field].id
                    else:
                        new_line[mapping_row.external_field] = product_line[mapping_row.internal_field]
                elif mapping_row.external_field and mapping_row.default_reference:
                    new_line[mapping_row.external_field] = mapping_row.default_reference.id

            if (len(new_line) == 0):
                continue

            if self.target_document_model == 'stock.picking':
                new_line['company_id'] = self.env.company.id
                new_line['partner_id'] = self.env.company.partner_id.id
                new_line['picking_type_id'] = self.env.ref('stock.picking_type_internal').id
                new_line['location_id'] = internal_transfer_defaults['location_id']
                new_line['location_dest_id'] = internal_transfer_defaults['location_dest_id']

            if self.target_document_model == 'purchase.order':
                new_line['name'] = self._get_product_purchase_description(product_line['product'])

            if self.target_document_model == 'product.pricelist':
                # new_line['date_start'] = fields.Datetime.now()
                new_line['display_applied_on'] = '1_product'
                # new_line['applied_on'] = '1_product'
                new_line['applied_on'] = '0_product_variant'
                # new_line['applied_on'] = False
                new_line['compute_price'] = 'fixed'
                # new_line['compute_price'] = 'percentage'
                new_line['company_id'] = self.env.company.id

            if self.target_document_model == 'sale.order':
                # new_line['recompute_delivery_price'] = False
                new_line['product_updatable'] = False

            document.update({
                self.document_lines_field_name: [(fields.Command.create(new_line))]
            })

        return document
