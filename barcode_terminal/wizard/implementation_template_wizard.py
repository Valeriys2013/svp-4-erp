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


class ImplementationTemplateWizard(models.Model):
    _name = 'barcode_terminal.implementation_template_wizard'
    _description = 'Draft generator of implementation mapping templates'

    name = fields.Char()

    @api.model
    def _model_is_user_creatable_document(self, model_id):
        mf = self.env[model_id].fields_get(attributes=['relation'])
        for f_key in mf:
            if (mf[f_key].get('relation') == 'res.users'):
                return True
        return False

    @api.model
    def _model_collection_of_product_lines(self, line_model_id):
        mf = self.env[line_model_id].fields_get(attributes=['name', 'type', 'string', 'relation', 'relation_field'])
        # print(self.env['barcode_terminal.barcode_collection'].fields_get(attributes=['relation_field']))
        # print(self.env['barcode_terminal.barcode_collection'].fields_get(attributes=['type','string','relation']))
        has_product = False
        product_field = ''
        result = []
        for f_key in mf:
            f_attrs = mf[f_key]
            if (f_attrs['type'] == 'many2one' and f_attrs['relation'] == 'product.product'):
                has_product = True
                product_field = f_key
                break
        if (not has_product):
            return result
        for f_key in mf:
            f_attrs = mf[f_key]
            if (f_attrs['type'] == 'many2one'):
                possible_parent_doc = f_attrs['relation']
                possible_relation_field = f_attrs['name']
                rmf = self.env[possible_parent_doc].fields_get(
                    attributes=['type', 'relation_field', 'string', 'relation', 'name'])
                for parent_f_k, parent_f_attrs in rmf.items():
                    # print("parent_f_attrs>>>>>>>>>>>>>>", parent_f_attrs)
                    if (parent_f_attrs.get('relation_field') == possible_relation_field
                            and parent_f_attrs['relation'] == line_model_id
                            and parent_f_attrs['type'] == 'one2many'):
                        # print(' :: line_model_id - ',line_model_id,' :: possible_parent_doc - ',possible_parent_doc,' :: possible_relation_field - ',possible_relation_field,' :: product_field - ',product_field,)
                        result.append({"id": possible_parent_doc, "descript_lines_field": parent_f_attrs.get('string'),
                                       "id_lines_field": parent_f_attrs.get('name')})
        # print(' :: result - ', result)
        return result
        # return parent_doc_relation

    def _get_collection_description(self, model_id):
        mf = self.env[model_id].fields_get(allfields=['description'], attributes=['string'])
        model_description = mf['description']['string']
        return model_description

    @api.model
    def _get_target_models_data(self):
        product_line_models = {}
        for model_item in self.pool.models.items():
            line_model_id = model_item[0]
            for collection_doc in self._model_collection_of_product_lines(line_model_id):
                collection_doc_id = collection_doc['id']

                collection_model_ids = self.env['ir.model'].search(
                    [('model', '=', collection_doc_id)], limit=1)
                collection_model_id = collection_model_ids[:1]
                collection_model_name = collection_model_id['name']

                multi_line_field_label = collection_doc['descript_lines_field']
                multi_line_field_id = collection_doc['id_lines_field']
                if (self._model_is_user_creatable_document(collection_doc_id)):
                    target_name = collection_model_name + " [" + multi_line_field_label + "]"
                    target_key = collection_doc_id + " [" + multi_line_field_id + "]"
                    # target_key = collection_doc_id + " (" + line_model_id + ")"
                    # product_line_models[target_name] = {"line_model_id": line_model_id,
                    product_line_models[target_key] = {"line_model_id": line_model_id,
                                                        "line_field_name": multi_line_field_id,
                                                        "target_name": target_name,
                                                        "collection_doc_id": collection_doc_id}
        return product_line_models

    @api.model
    def _selection_target_models(self):
        return [(k, v['target_name']) for k,v in sorted(self._get_target_models_data().items(), key = lambda x: x[1]['target_name'])]
        # return [(k, k) for k in sorted(self._get_target_models_data().keys())]

    @api.depends('name')
    def _compute_target_models_data(self):
        for document in self:
            document.target_models_data = document._get_target_models_data()
            # print("zzz", document.target_models_data)

    # active = fields.Boolean("Active?", default=True)
    target_models_data = fields.Binary(string='Possible target models', compute=_compute_target_models_data)

    target_document_model = fields.Char('Target document model', )
    # document_model_id = fields.Many2one('ir.model', )
    target_doc_line_model = fields.Char('Target document line model', )
    document_lines_field_name = fields.Char('Target document multi-line field', )
    # target_doc_line_model = fields.Many2one('ir.model', )
    external_model_sel = fields.Selection(_selection_target_models, string="External model selection")
    # external_model_field_sel = fields.Selection(_selection_target_models_fields, string="External model fielf")

    @api.onchange('external_model_sel')
    def _onchange_external_model_sel(self):
        if not self.external_model_sel:
            return
        for document in self:
            # document.line_ids.clear()
            dic = document.target_models_data[self.external_model_sel]
            product_line_model = dic['line_model_id']
            product_collection_model = dic['collection_doc_id']
            product_lines_field = dic['line_field_name']
            self.name = dic['target_name']
            # print('product_line_model ', product_line_model)
            # print('product_collection_model ', product_collection_model)
            # print('product_lines_field ', product_lines_field)
            # print('timestamp ', self.env.context['timestamp'])

            document.target_doc_line_model = product_line_model
            document.target_document_model = product_collection_model
            document.document_lines_field_name = product_lines_field
    #
    @api.model
    def create_implementation_template(self, target_document_model, document_lines_field_name, template_name, forced_creation=False):
        # print("!!!!!!!!!!!!!!!!!!!!!!!!!!")
        # for rec in self:
        #     rec.write({'doc_attrib_ids': [(5, 0, 0)]})
        # document.write({'doc_attrib_ids': [(5, 0, 0)]})
        # model_ = self.env['sale.order.template']

        # flds = self.env[product_collection_model].fields_get()
        # print(flds)
        try:
            print('target_document_model -', target_document_model)
            target_document_model_ids = self.env['ir.model'].search(
                [('model', '=', target_document_model)], limit=1)
            target_document_model_id = target_document_model_ids[:1]

            document_lines_field_ids = self.env['ir.model.fields'].search(
                [('model', '=', target_document_model), ('name', '=', document_lines_field_name)], limit=1)
            document_lines_field_id = document_lines_field_ids[:1]

            target_doc_line_model = document_lines_field_id.relation
            formated_name = 'barcode_terminal.implementation_template_' + target_document_model + "." + document_lines_field_name

            dic = {}
            dic['target_document_model_id'] = target_document_model_id.id
            dic['document_lines_field_id'] = document_lines_field_id.id
            dic['target_doc_line_model'] = target_doc_line_model
            dic['target_document_model'] = target_document_model

            if forced_creation:
                dic['forced_creation'] = True

            dic['document_lines_field_name'] = document_lines_field_name
            # xml_id = formated_name#not working
            # dic['id'] = xml_id#.replace('.','_')
            dic['autocreate_identifier'] = formated_name
            # dic['doc_attrib_ids'] =  [(5, 0, 0)]
            existing_templates = self.env['barcode_terminal.implementation_field_mapping'].search(
                [('autocreate_identifier', '=', formated_name)], limit=1)
            existing_template = existing_templates[:1]

            model_ = self.sudo(True).env[target_document_model]
            dmf = model_.fields_get(
                attributes=['name', 'string', 'readonly', 'required', 'relation', 'type'])
            # print('dmf ', dmf)
            # doc_attribs = []

        except KeyError as kerr:
            print("Error when creating template: Model not found - ", target_document_model)
            return
        except:
            print("Something went wrong when creating template - ", template_name)
            return
        else:
            pass

        try:
            mf = self.sudo(True).env[target_doc_line_model].fields_get(
                attributes=['name', 'string', 'readonly', 'required', 'relation', 'type'])
            # print('mf ', mf)
        except KeyError as kerr:
            print('document_lines_field_name -', document_lines_field_name)
            print("Error when creating template: Model not found - ", target_doc_line_model)
            return
        except:
            print("Something went wrong when creating template - ", template_name)
            return
        else:
            pass

        if not existing_template:
            document = self.env['barcode_terminal.implementation_field_mapping'].create(dic)
        else:
            existing_template.update(dic)
            document = existing_template
            # document = self.env['barcode_terminal.implementation_field_mapping'].update(existing_template , dic)


        document.write({'doc_attrib_ids': [(5, 0, 0)]})
        for f_key in dmf:
            attrs = dmf[f_key]

            external_field_ids = self.env['ir.model.fields'].search(
                [('model', '=', target_document_model), ('name', '=', f_key)], limit=1)
            external_field_id1 = external_field_ids[:1]
            is_readonly = attrs['readonly']
            is_required = attrs['required']
            is_product_related = attrs['type'] == 'many2one' and "product" in attrs['relation']
            is_product = attrs['type'] == 'many2one' and "product.product" == attrs['relation']
            is_product_template = attrs['type'] == 'many2one' and "product.template" == attrs['relation']
            is_uom = attrs['type'] == 'many2one' and "uom.uom" in attrs['relation']
            some_kind_of_price = attrs['type'] == 'float' and "price" in f_key
            some_quantity = attrs['type'] == 'float' and "quantity" in f_key
            is_transfer_picking_type = attrs['type'] == 'many2one' and 'picking_type_id' == attrs['name']
            is_name = attrs['type'] == 'char' and "name" in attrs['name']
            is_primitive = (attrs['type'] == 'integer' or attrs['type'] == 'float' or attrs['type'] == 'char'
                            or attrs['type'] == 'text' or attrs['type'] == 'datetime' or attrs['type'] == 'date')
            is_date = attrs['type'] == 'datetime' or attrs['type'] == 'date'

            # if (is_readonly and not is_product and not is_uom and not is_transfer_picking_type):
            if (is_readonly and not is_product_related and not is_uom):
                continue
            # if (not is_required and not is_product and not is_uom and not is_name and not is_transfer_picking_type):
            if (not is_required and not is_product_related and not is_uom and not is_name):
                continue
            if (not is_primitive and not is_product_related and not is_uom):
                continue
            internal_field = ""
            if is_name:
                internal_field = "name"
            elif is_date:
                internal_field = "create_date"
            vals = {'external_field_id': external_field_id1.id, 'external_field': f_key,
                    'external_field_type': attrs['type'], 'internal_field': internal_field}
            # print('vals !!!!//////////// ', vals)
            document.update({
                'doc_attrib_ids': [(fields.Command.create(vals))]
            })

        # todo set meaningful defaults where possible

        document.write({'prod_line_ids': [(5, 0, 0)]})

        # parent_doc_line_vals = []
        for f_key in mf:
            external_field_ids1 = self.env['ir.model.fields'].search(
                [('model', '=', target_doc_line_model), ('name', '=', f_key)], limit=1)
            external_field_id1 = external_field_ids1[:1]

            attrs = mf[f_key]

            is_readonly = attrs['readonly']
            is_required = attrs['required']
            is_product_related = attrs['type'] == 'many2one' and "product" in attrs['relation']
            is_product = attrs['type'] == 'many2one' and "product.product" == attrs['relation']
            is_product_template = attrs['type'] == 'many2one' and "product.template" == attrs['relation']
            is_uom = attrs['type'] == 'many2one' and "uom.uom" in attrs['relation']
            is_price = attrs['type'] == 'float' and "price" in attrs['name']
            is_description = attrs['type'] == 'char' and "name" in attrs['name']
            # is_description_picking = attrs['type'] == 'text' and "description_picking" in attrs['name']
            is_quantity = attrs['type'] == 'float' and ("quantity" in attrs['name'] or "_qty" in attrs['name'])
            is_primitive = (attrs['type'] == 'integer' or attrs['type'] == 'float' or attrs['type'] == 'char'
                            or attrs['type'] == 'text' or attrs['type'] == 'datetime' or attrs['type'] == 'date')
            if (is_readonly and not is_product_related and not is_uom):
                continue
            if (not is_required and not is_product_related and not is_uom and not is_price and not is_quantity):
                continue
            if (not is_primitive and not is_product_related and not is_uom):
                continue
            if target_document_model == 'product.pricelist' and is_price and "fixed_price" not in attrs['name']:
                continue

            internal_field = ""
            if is_product:
                internal_field = "product"
            elif is_product_template:
                internal_field = "product_tmpl_id"
            elif is_uom:
                internal_field = "uom_id"
            elif is_price:
                internal_field = "price_unit"
            elif is_quantity:
                if target_doc_line_model == 'stock.move' and attrs['name'] != 'product_uom_qty':
                    pass
                else:
                    internal_field = "quantity"
            elif is_description:#needed just for v.17(transfer template)
                internal_field = "barcode_name"

            new_line = {'external_field_id': external_field_id1.id, 'external_field': f_key,
                        'external_field_type': attrs['type'], 'internal_field': internal_field}
            # print('new_line>>>>', new_line)

            document.update({
                'prod_line_ids': [(fields.Command.create(new_line))]
            })
            # print('lines ', lines)
            # todo set meaningful defaults where possible

        document['name'] = template_name
        # message = "External model is %s" % (external_model_sel or "")
        # print(message)
        # return {
        #     'type': 'ir.actions.client',
        #     'tag': 'reload',
        # }

    def generate_implementation_template(self):
        # print("!!!!!!!!!!!!!!!!!!!!!!!!!!")
        # for rec in self:
        #     rec.write({'doc_attrib_ids': [(5, 0, 0)]})
        # document.write({'doc_attrib_ids': [(5, 0, 0)]})

        # flds = self.env[product_collection_model].fields_get()
        # print(flds)
        ctx = self.env.context.copy()
        # dic = {}

        target_document_model_ids = self.env['ir.model'].search(
            [('model', '=', self.target_document_model)], limit=1)
        target_document_model_id = target_document_model_ids[:1]

        # target_doc_line_model_ids = self.env['ir.model'].search(
        #     [('model', '=', self.target_doc_line_model)], limit=1)
        # target_doc_line_model_id = target_doc_line_model_ids[:1]

        document_lines_field_ids = self.env['ir.model.fields'].search(
            [('model', '=', self.target_document_model), ('name', '=', self.document_lines_field_name)], limit=1)
        document_lines_field_id = document_lines_field_ids[:1]

        pref_record = self.env['barcode_terminal.implementation_field_mapping'].ensure_find_allow_forced_creation()
        ctx['default_param_ref_allow_forced'] = pref_record
        ctx['default_target_doc_line_model'] = self.target_doc_line_model
        ctx['default_target_document_model_id'] = target_document_model_id.id
        ctx['default_target_document_model'] = self.target_document_model
        ctx['default_document_lines_field_id'] = document_lines_field_id.id
        ctx['default_document_lines_field_name'] = self.document_lines_field_name
        ctx['default_timestamp'] = self.env.context['timestamp']
        # dic['doc_attrib_ids'] =  [(5, 0, 0)]
        # document = self.env['barcode_terminal.implementation_field_mapping'].create(dic)

        dmf = self.env[self.target_document_model].fields_get(
            attributes=['name', 'string', 'readonly', 'required', 'relation', 'type'])
        # print('dmf ', dmf)
        doc_attribs = []
        for f_key in dmf:
            attrs = dmf[f_key]

            external_field_ids = self.env['ir.model.fields'].search(
                [('model', '=', self.target_document_model), ('name', '=', f_key)], limit=1)
            external_field_id1 = external_field_ids[:1]
            # external_field_id = external_field_ids[0]
            # vals = {'external_field': f_key,
           # 'external_field_type': attrs['type'],'external_field_rel': attrs.get('relation'), 'internal_field': ''}
            is_readonly = attrs['readonly']
            is_required = attrs['required']
            is_product_related = attrs['type'] == 'many2one' and "product" in attrs['relation']
            is_product = attrs['type'] == 'many2one' and "product.product" == attrs['relation']
            is_product_template = attrs['type'] == 'many2one' and "product.template" == attrs['relation']
            is_uom = attrs['type'] == 'many2one' and "uom.uom" in attrs['relation']
            some_kind_of_price = attrs['type'] == 'float' and "price" in f_key
            some_quantity = attrs['type'] == 'float' and "quantity" in f_key
            is_transfer_picking_type = attrs['type'] == 'many2one' and 'picking_type_id' == attrs['name']
            is_name = attrs['type'] == 'char' and "name" in attrs['name']
            is_primitive = (attrs['type'] == 'integer' or attrs['type'] == 'float' or attrs['type'] == 'char'
                            or attrs['type'] == 'text' or attrs['type'] == 'datetime' or attrs['type'] == 'date')
            is_date = attrs['type'] == 'datetime' or attrs['type'] == 'date'

            # if (is_readonly and not is_product and not is_uom and not is_transfer_picking_type):
            if (is_readonly and not is_product_related and not is_uom):
                continue
            # if (not is_required and not is_product and not is_uom and not is_name and not is_transfer_picking_type):
            if (not is_required and not is_product_related and not is_uom and not is_name):
                continue
            if (not is_primitive and not is_product_related and not is_uom):
                continue
            internal_field = ""
            # if is_product:
            # internal_field = "product"
            # elif is_uom:
            #     internal_field = "uom_id"
            # elif some_kind_of_price:
            #     internal_field = "price_unit"
            # elif some_quantity:
            #     internal_field = "quantity"
            if is_name:
                internal_field = "name"
            elif is_date:
                internal_field = "create_date"


            vals = {'external_field_id': external_field_id1.id, 'external_field': f_key,
                    'external_field_type': attrs['type'], 'internal_field': internal_field}

            # print(vals)
            # print('vals !!!!//////////// ', vals)
            # doc_attribs.append((0, 0, vals))
            # document.update({
            #     'doc_attrib_ids': [(fields.Command.create(vals))]
            # })
            doc_attribs.append(fields.Command.create(vals))
        ctx.update({
            'default_doc_attrib_ids': doc_attribs,
        })

        # document.doc_attrib_ids = doc_attribs
        # print('doc_attribs ', doc_attribs)

        # todo set meaningful defaults where possible

        # for rec in self:
        #     rec.write({'prod_line_ids': [(5, 0, 0)]})
        # document.write({'prod_line_ids': [(5, 0, 0)]})
        mf = self.env[self.target_doc_line_model].fields_get(
            attributes=['name', 'string', 'readonly', 'required', 'relation', 'type'])
        # print('mf ', mf)

        parent_doc_line_vals = []
        for f_key in mf:
            external_field_ids1 = self.env['ir.model.fields'].search(
                [('model', '=', self.target_doc_line_model), ('name', '=', f_key)], limit=1)
            external_field_id1 = external_field_ids1[:1]

            attrs = mf[f_key]
            # document.line_ids.append({'external_field': f_key})

            # if attrs['type'] == 'many2one':
            #     default_ref = '% s,% s' % (attrs['relation'], 0)
            #     new_line['default_reference'] = default_ref

            is_readonly = attrs['readonly']
            is_required = attrs['required']
            is_product_related = attrs['type'] == 'many2one' and "product" in attrs['relation']
            is_product = attrs['type'] == 'many2one' and "product.product" == attrs['relation']
            is_product_template = attrs['type'] == 'many2one' and "product.template" == attrs['relation']
            is_uom = attrs['type'] == 'many2one' and "uom.uom" in attrs['relation']
            is_price = attrs['type'] == 'float' and "price" in attrs['name']
            is_quantity = attrs['type'] == 'float' and ("quantity" in attrs['name'] or "_qty" in attrs['name'])
            is_primitive = (attrs['type'] == 'integer' or attrs['type'] == 'float' or attrs['type'] == 'char'
                            or attrs['type'] == 'text' or attrs['type'] == 'datetime' or attrs['type'] == 'date')
            is_description = attrs['type'] == 'char' and "name" in attrs['name']
            # is_description_picking = attrs['type'] == 'text' and "description_picking" in attrs['name']

            if (is_readonly and not is_product_related and not is_uom):
                continue
            if (not is_required and not is_product_related and not is_uom and not is_price and not is_quantity):
                continue
            if (not is_primitive and not is_product_related and not is_uom):
                continue

            internal_field = ""
            if is_product:
                internal_field = "product"
            elif is_product_template:
                internal_field = "product_tmpl_id"
            elif is_uom:
                internal_field = "uom_id"
            elif is_price:
                internal_field = "price_unit"
            elif is_description:
                internal_field = "barcode_name"
            elif is_quantity:
                if self.target_doc_line_model == 'stock.move' and attrs['name'] != 'product_uom_qty':
                    pass
                else:
                    internal_field = "quantity"
            new_line = {'external_field_id': external_field_id1.id, 'external_field': f_key,
                        # new_line = {'external_field': f_key,
                        'external_field_type': attrs['type'], 'internal_field': internal_field}
            # new_line = {'external_field_id': external_field_id,'external_field': f_key,'external_field_name': attrs['string'],'external_field_type': attrs['type'], 'internal_field': ''}
            # print('new_line>>>>', new_line)

            # parent_doc_line_vals.append((0,0,new_line))
            # print('parent_doc_line_vals ', parent_doc_line_vals)
            # document.prod_line_ids = parent_doc_line_vals
            parent_doc_line_vals.append(fields.Command.create(new_line))
        ctx.update({
            'default_prod_line_ids': parent_doc_line_vals,
        })

            # todo set meaningful defaults where possible
        # self.external_model_sel
        # string_value = dict(self.fields_get(allfields=['external_model_sel'], attributes=['selection']).get('selection')).get(self.external_model_sel)
        ctx['default_name'] = self.name
        # ctx['default_name'] = self.external_model_sel
        # message = "External model is %s" % (self.external_model_sel or "")
        # print(message)
        # print('document_dic ', document)
        # new_template_id = self.env['barcode_terminal.implementation_field_mapping'].create(document)
        return {
            'name': 'New Implementation Template : ' + self.external_model_sel,
            "views": [[False, "form"]],
            # 'view_type': 'form',
            'view_mode': 'form',
            'res_model': "barcode_terminal.implementation_field_mapping",
            'view_id': False,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': ctx
        }

