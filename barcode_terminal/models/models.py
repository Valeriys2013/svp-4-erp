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


import base64
import os

from odoo import models, fields, api

from odoo.osv import osv
import re


class BarcodeCollection(models.Model):
    _name = "barcode_terminal.barcode_collection"
    _description = "Barcode collection"
    # _inherit = ['image.mixin', 'mail.alias.mixin', 'mail.thread']
    _inherit = ['image.mixin', 'mail.thread']

    name = fields.Char()
    collection_comment = fields.Text("Collection comment")
    start_timestamp = fields.Char("Original start")
    create_date = fields.Datetime("Created", default=lambda self: fields.Datetime.now())
    active = fields.Boolean("Active?", default=True)
    source_id = fields.Many2one(
    "barcode_terminal.import_field_mappings", string="Import file type"
    )
    state = fields.Selection(
        selection=[
            ('draft', "Loaded"),
            ('found_nothing', "Nothing found"),
            ('part_recognized', "Part recognized"),
            ('all_recognized', "All recognized"),
            ('implemented', "Implemented"),
            # ('done', "Locked"),
            # ('cancel', "Cancelled"),
        ],
        string="Status",
        readonly=True, copy=False, index=True,
        tracking=True,
        default='draft')

    line_ids = fields.One2many(
    "barcode_terminal.barcode_collection.line",
    "collection_id",
    string="Barcoded goods items",
    )
    implementation_ids = fields.One2many(
    "barcode_terminal.implementation",
    "source_collection_id",
    string="Implementations of collection",
    )
    ext_id = fields.Char(string="Version", compute="compute_external_id", store=True, readonly=True)
    version = fields.Char(string="Version", readonly=True)
    user_id = fields.Many2one(
        comodel_name='res.users',
        string="Responsible",
        # compute='_compute_user_id',
        default=lambda self: self.env.user,
        store=True, readonly=False,  index=True
        )
    def _compute_user_id(self):
        return self.env.user
        # return self.env.uid

    @api.depends('name')
    def compute_external_id(self):
        res = self.get_external_id()
        for record in self:
            record['ext_id'] = res.get(record.id)
            # if loaded automatically by alias
            if not record['ext_id']:
                record['ext_id'] = record['version']

    enable_implementation = fields.Boolean(compute ="compute_implementation_available", default = True)

    @api.depends('line_ids')
    def compute_implementation_available(self):
        product_found = self.env['barcode_terminal.barcode_collection.line'].search([('collection_id', '=', self.ids[0] ), ('product', '!=', False)])
        if product_found:
            return True
        else:
            return False
    def try_something(self):
        model_1 = self.env['sale.order.template']
        # print('model_--',model_1)

        params = self.env['ir.config_parameter'].sudo()
        allow_forced_creation = params.get_param('barcode_terminal.allow_forced_creation')
        print('allow_forced_creation --- ', allow_forced_creation)

    def try_load_file(self):
        val = {
            'docs': self,
        }
        html = self.pool["ir.ui.view"].render(self.env.cr, self.env.uid,
                                              'base_import.ImportView, val,'
                                              ' engine="ir.qweb", context=self.env.context).decode("utf8")')
        return html

    # def MoreOptions(self):
    #     print("MoreOptions() called")
    #     return "zzz"

    def generate_msg(self, context=None):
        raise osv.except_osv("Warning!", " Hello !!.")

    def find_barcoded_products(self):
        for collection in self:
            found_cnt = 0
            not_found_cnt = 0
            for row in collection.line_ids:
                if not row['barcode']:
                    continue
                product_product_id = (self.env['product.product'].
                                      search([('barcode', '=', row['barcode'])], limit=1))
                if product_product_id:
                    row.product = product_product_id # this way it saved in database as well - not clear why?
                    row.uom_id = row.product.uom_id
                    found_cnt +=1
                else: not_found_cnt += 1

            # print('imp cnt', "---", len(self.implementation_ids))
            if (len(self.implementation_ids) >0):
                self.state = 'implemented'
            elif found_cnt == 0:
                self.state = 'found_nothing'
            elif not_found_cnt > 0:
                self.state = 'part_recognized'
            else: self.state = 'all_recognized'
            #self = self.with_context(cxt_state=self.state)

    def generate_new_products(self):
        for collection in self:
            found_cnt = 0
            created_cnt = 0
            for row in collection.line_ids:
                    if not row['barcode']:
                        continue
                    product_product_id = (self.env['product.product'].
                                          search([('barcode', '=', row['barcode'])], limit=1))
                    if not product_product_id:
                        new_product_name = row['barcode_name']
                        if not new_product_name:
                            new_product_name = "sku_" +row['barcode']
                        product_product_id = self.env['product.product'].create({'name':new_product_name,'barcode':row['barcode'],
                                                                                 'uom_id':row['uom_id'].id,'standard_price':row['price_unit'],
                                                                                 'image_1920':row['image_1920'],})

                        row.product = product_product_id # this way it saved in database as well - not clear why?
                        # row.uom_id = row.product.uom_id
                        created_cnt += 1
                    elif row['product'] != False: found_cnt +=1

            if (len(self.implementation_ids) > 0):
                self.state = 'implemented'
            elif found_cnt + created_cnt == len(collection.line_ids):
                self.state = 'all_recognized'
            elif found_cnt + created_cnt == 0:
                self.state = 'found_nothing'
            elif found_cnt + created_cnt < len(collection.line_ids):
                self.state = 'part_recognized'
            # else: self.state = 'all_recognized'

    # file - of type FileStorage
    @api.model
    def model_fun_for_rpc(self, domain):
        records = self.search(domain or [], offset=0, limit=1)
        if not records:
            return {'greeting': "Hello from python _^-^-^-^-8)))",}


        data = {
            # 'uid': uid,
            'greeting': "Hello from python _^-^-^-^-8)))",
            'record_name': records[0].name,  #self.name,
            'record_version': records[0].ext_id,
        }
        return data

    def test_function(self):
        data = self.find_self_implementations();
        print("find_self_implementations >>>",data)

    def action_upload_wizard(self):
        return {'type': 'ir.actions.act_window',
                'name': 'Upload BarcodeCollector data',
                'res_model': 'barcode_terminal.import_zip_dialog',
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                'context': {'default_user_id': self.user_id}, }

    def action_implement_wizard(self):
        print("self._ids", self._ids[0])
        return {'type': 'ir.actions.act_window',
                'name': 'New implementation',
                'res_model': 'barcode_terminal.implementation_wizard',
                'target': 'new',
                'view_mode': 'form',
                'view_type': 'form',
                'context': {'default_user_id': self.user_id, 'default_source_collection_id': self._ids[0]}}

    # def on_close(self):
    #     self.MoreOptions()

    @api.model
    def get_record_state(self, domain):
        records = self.search(domain or [], offset=0, limit=1)
        if not records:
            return {}
        res = {'record_state': records[0].state,
               }
        return res

    @api.model
    def find_newest_collection(self):
        records = self.search([], offset=0, limit=1, order='id desc')
        latest_id = records[:1]
        # print('latest_id--^-^-8', latest_id.id )
        return {'latest_id': latest_id.id}

    @api.model
    def find_newest_record(self, model):
        records = self.search([('model', '=', model)], offset=0, limit=1, order='id desc')
        latest_id = records[:1]
        # print('latest_id--^-^-8', latest_id.id )
        return {'latest_id': latest_id.id}

    @api.model
    def find_new_implementations(self, domain):
        records = self.search(domain or [], offset=0, limit=1)
        if not records:
            return {}
        res = {'greeting': "Hello from python _^-^-^-^-8)))",
               'record_name': records[0].name,  # self.name,
               'record_version': records[0].ext_id,
               }
        for rec in records:
            implementation_lines = self.env['barcode_terminal.implementation'].search(
                [('source_collection_id', '=', rec._ids[0]), ("document_reference", '=', False)])
            for uncompleted_line in implementation_lines:
                wizard_start = uncompleted_line.wizard_start
                target_document_model = uncompleted_line.target_document_model
                new_docs = self.env[target_document_model].search(
                    [('create_date', '>=', wizard_start), ('create_uid', '=', self.env.uid)],  order="create_date desc", limit=1)

                if new_docs:
                    new_doc = new_docs[:1]
                    # print("target_document_model", target_document_model);
                    if (target_document_model == 'sale.order'):
                        if not new_doc['state']:
                            new_doc['state'] = 'draft'

                    res['new_doc'] = new_doc #just to workaround issue with '_onchange_company_id_warning'
                    # method in "sale.order" which hang  the program into endless loop
                    uncompleted_line.document_reference = new_doc
                    uncompleted_line.result_doc_name = new_doc.display_name
                else:
                    print("no doc")
                    uncompleted_line.unlink()

        # if res['new_doc']:
        if ('new_doc' in res):
            rec.state = 'implemented'
            # print("rec.state", self.state);

        return res
        # return {
        #     'type': 'ir.actions.client',
        #     'tag': 'reload',
        # }

    def find_self_implementations(self):
        res = {'greeting': "Hello from python _^-^-^-^-8)))",
               'record_name': self.name,  # self.name,
               'record_version': self.ext_id,
               }
        # print("self.user_id---", self.user_id.id)
        # print("self.env.uid---", self.env.uid)
        for rec in self:
            # print("rec.user_id---", rec.user_id.id)
            implementation_lines = self.env['barcode_terminal.implementation'].search(
                [('source_collection_id', '=', rec._ids[0]), ("document_reference", '=', False)])
            for uncompleted_line in implementation_lines:
                wizard_start = uncompleted_line.wizard_start
                target_document_model = uncompleted_line.target_document_model
                # print("target_document_model ---", target_document_model)
                # print("wizard_start ---", wizard_start)
                new_docs = self.env[target_document_model].search(
                    [('create_date', '>=', wizard_start), ('user_id', '=', self.env.uid)], limit=1)
                if new_docs:
                    new_doc = new_docs[:1]
                    # print("new_doc", new_doc);
                    res['new_doc'] = new_doc
                    uncompleted_line.document_reference = new_doc
                else:
                    print("no doc")
                    uncompleted_line.unlink()

        return res

    def update_product_standard_prices(self):
        # print("update_product_standard_prices in ", self.name)
        for collection in self:
            for line in collection.line_ids:
                if not line.product:
                    continue
                if line.price_unit == 0.0:
                    continue
                # print("price_unit = ", line.price_unit)
                line.product.standard_price = line.price_unit

    def update_product_images(self):
        # print("update_product_images in ", self.name)
        for collection in self:
            for line in collection.line_ids:
                if not line.product:
                    continue
                if not line.image_1920:
                    continue
                # print("price_unit = ", line.price_unit)
                line.product.image_1920 = line.image_1920
                # line.product.image_1024 = line.image_1024

    def assign_product_images(self):
        # print("update_product_images in ", self.name)
        for collection in self:
            for line in collection.line_ids:
                if not line.product:
                    continue
                if not line.image_1920:
                    continue
                if line.product.image_1920:
                    continue #assign images where they are absent only
                # print("price_unit = ", line.price_unit)
                line.product.image_1920 = line.image_1920
                # line.product.image_1024 = line.image_1024

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        # print('custom_values1 :', custom_values)
        self = self.with_context(default_user_id=False)
        if custom_values is None:
            custom_values = {}
        subject_prefix = custom_values['subject_prefix'] or "barcodecollector data"
        attachment_prefix = custom_values['attachment_prefix'] or ""
        regex_s = re.compile("^" + subject_prefix + "(.*)")
        # regex = re.compile("^barcodecollector data(.*)")
        # regex = re.compile("^\[(.*)\]")
        subj = msg_dict.get('subject')
        if subject_prefix:
            match = regex_s.match(subj)
            if match == None:
                return False
        # match1 = match.group(1)
        # if match1 != None:
        # print('subj: ', subj)
        # print('msg_dict.keys: ', msg_dict.keys())
        if msg_dict['attachments']:
            attached_file_name = msg_dict['attachments'][0][0]
            attached_file_content = msg_dict['attachments'][0][1]
            if attachment_prefix:
                regex_a = re.compile("^" + attachment_prefix + "(.*)")
                match2 = regex_a.match(attached_file_name)
                if match2 == None:
                    return False

            custom_values = self.env['barcode_terminal.alias_data_import'].import_raw_zip_csv_xls_file(attached_file_content, attached_file_name)
            # print('custom_values2 ', custom_values)
        if not custom_values:
            print("Probably repeating import attempt>>>",subj)
            empty_col_name = "Rejected import :" + subj
            custom_values['name'] = empty_col_name
            # return False//Good: no clone records created ; bad : email messages remain as new and next time are tried to be imported again
        return super(BarcodeCollection, self).message_new(msg_dict, custom_values)


class CollectionLine(models.Model):
    _name = "barcode_terminal.barcode_collection.line"
    _description = "Barcode collection line"
    _inherit = ['image.mixin']
    _sql_constraints = [('barcode_unique', 'check(1=1)', "no error")]
    # _sql_constraints = [('barcode_unique', 'unique(collection_id,barcode)', "Barcode must be unique for each document line.!")]
    collection_id = fields.Many2one(
        "barcode_terminal.barcode_collection",
        required=True, ondelete='cascade'
    )

    barcode = fields.Char("Barcode")
    barcode_name = fields.Char("Name(external)")
    barcode_comment = fields.Char("Comment(external)")
    quantity = fields.Integer("Quantity")
    # image = fields.Image("Image", max_width=1920, max_height=1920) #instead this using image_1920 from image.mixin

    def _get_default_uom_id(self):
        return self.env.ref('uom.product_uom_unit')

    uom_id = fields.Many2one(
        'uom.uom', 'UoM',
        default=_get_default_uom_id,
        help="Unit of measure.(if not selected - default will be used)")

    #todo: refactor to product_id
    product = fields.Many2one("product.product")#cmpute does not work this way - probably unfixed bug for One2many submodels
    # product = fields.Many2one("product.product", compute="_compute_product_by_barcode", store=True)
    product_tmpl_id = fields.Many2one('product.template',
        string="Product template", related='product.product_tmpl_id')

    product_image = fields.Binary("Product image", related='product.image_1024')
    price_unit = fields.Float(
        string="Unit Price")

    @api.onchange('product')
    def onchange_product_id(self):
        if not self.product:
            return
        # self.uom_id = self.product.uom_po_id or self.product.uom_id
        self.uom_id = self.product.uom_id

    @api.depends("barcode")
    def _compute_product_by_barcode(self):
        for row in self:
            product_product_id = (self.env['product.product'].
                                  search([('barcode', '=', row['barcode'])], limit=1))
            # print(row['barcode'])
            if product_product_id:
                row.product = product_product_id

    def assign_barcode(self):
        if self.product == False:
            return
        if self.product.barcode != False:
            return
        for prod in self.product:
            prod.barcode = self.barcode
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def update_all(self):
        if self.product == False:
            return
        if self.product.barcode and self.product.barcode != self.barcode:
            return
        for prod in self.product:
            prod.name = self.barcode_name
            prod.image_1920 = self.image_1920
            prod.image_1024 = self.image_1024
            prod.standard_price = self.price_unit
            if not self.product.barcode:
                prod.barcode = self.barcode

        for record in self:
            record.product_image = self.image_1024
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }


    def replace_existing_image(self):
        if self.product == False:
            return
        if self.product.barcode != self.barcode:
            return
        for prod in self.product:
            prod.image_1920 = self.image_1920
            prod.image_1024 = self.image_1024
        for record in self:
            record.product_image = self.image_1024
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }


class ImportlFieldMappingLine(models.Model):
    _name = "barcode_terminal.import_field_mappings.line"
    _description = "Import field mapping line"
    mapping_id = fields.Many2one(
        "barcode_terminal.import_field_mappings",
        required=True, ondelete='cascade'
    )

    internal_field = fields.Char("InternalField")
    external_field = fields.Char("ExternalField")


class ImportFieldMapping(models.Model):
    _name = "barcode_terminal.import_field_mappings"
    _description = "Import field mapping"

    # external_model = fields.Char("Target document type")
    active = fields.Boolean("Active?", default=True)
    external_file_type = fields.Char("Import file type")

    line_ids = fields.One2many(
        "barcode_terminal.import_field_mappings.line",
        "mapping_id",
        string="Import field mapping lines",
    )
# =================================


# =================================




