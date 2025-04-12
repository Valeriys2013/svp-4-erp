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
from odoo.exceptions import UserError
import base64
import io
import os
from zipfile import ZipFile
import odoo.addons.base_import
from odoo.tools.safe_eval import datetime


class AliasDataImport(models.TransientModel):
    _name = 'barcode_terminal.alias_data_import'
    _description = 'Messages data import'
    _inherit = 'base_import.import'
    # name = fields.Char()
    loaded_filename = fields.Char()
    loaded_file = fields.Binary(string="Upload ZIP; CSV; XLS",
                                help='Zip files from Android app "SVP Barcode Collector"')
    model_fields = ['name', False, 'start_timestamp', 'version', 'collection_comment', 'line_ids/barcode',
                    'line_ids/barcode_name',
                    'line_ids/quantity', 'line_ids/barcode_comment', False, False, 'line_ids/image_1920',
                    'line_ids/price_unit']
    file_columns = ['taskname', 'rowcnt', 'starttime', 'endtime', 'taskcomment', 'code', 'name',
                    'quantity', 'comment', 'format', 'picturefile', 'b64picture', 'cost']
    file_columns_adapted = ['collection', 'rowcnt', 'starttime', 'version', 'collectioncomment', 'barcode', 'name',
                            'counted quantity', 'description', 'format', 'picturefile', 'image', 'cost']

    def import_raw_zip_csv_xls_file(self, decoded_b64_data, loaded_filename):
        tmp = loaded_filename.split('.')
        ext = tmp[len(tmp) - 1]
        custom_values = {}
        if ext == 'zip':
            buffer = io.BytesIO(decoded_b64_data)
            zip_data = ZipFile(buffer)
            name_list = zip_data.namelist()
            for data_file_name in name_list:
                tmp = data_file_name.split('.')
                data_f_ext = tmp[len(tmp) - 1]
                if data_f_ext == 'csv' or data_f_ext == 'xls':
                    data = zip_data.open(data_file_name)
                    data_b64 = base64.encodebytes(data.read())
                    # print("_import_zip_cvs_xls_files try zip : ")
                    custom_values = self.barcode_term_import(data_b64, data_file_name)
                else:
                    continue

        elif ext == 'csv' or ext == 'xls':
            # print('_import_zip_cvs_xls_files try : ')
            custom_values = self.barcode_term_import(self.loaded_file, loaded_filename)
        return custom_values

    def barcode_term_import(self, data_file, data_file_name):
        b64_data = base64.decodebytes(data_file)
        first_try_result = self.try_import_data("barcode_terminal.barcode_collection", b64_data, data_file_name,
                                                self.model_fields, self.file_columns)
        if first_try_result:
            return first_try_result
        second_try_result = self.try_import_data("barcode_terminal.barcode_collection", b64_data, data_file_name,
                                                 self.model_fields, self.file_columns_adapted)
        return second_try_result

    def try_import_data(self, res_model, data_file, data_file_name, model_fields, file_columns):

        OPTIONS = {'has_headers': True, 'advanced': True, 'keep_matches': False,
                   'name_create_enabled_fields': {}, 'import_set_empty_fields': [],
                   'import_skip_records': [], 'fallback_values': {}, 'skip': 0,
                   'limit': 2000, 'encoding': '', 'separator': '', 'quoting': '"',
                   'sheet': '', 'date_format': '', 'datetime_format': '',
                   'float_thousand_separator': ',', 'float_decimal_separator': '.', 'fields': []}

        import_wizard = self._create_import_record_with_data(res_model, data_file_name, data_file)
        file_length, rows = import_wizard._read_file(OPTIONS)
        if file_length <= 0:
            raise import_wizard.ImportValidationError("Import file has no content or is corrupt")
        count = 3
        preview = rows[:count]

        # Get file headers
        low_headers = []
        if OPTIONS.get('has_headers') and preview:
            # We need the header types before matching columns to fields
            headers = preview.pop(0)
            low_headers = [col.lower() for col in headers]
            # header_types = import_wizard._extract_headers_types(headers, preview, OPTIONS)
            try:
                ext_id_pos = low_headers.index(file_columns[3])
            except:
                print("Wrong data format: table should contain external identifier in column  :: ", file_columns[3])
                print("headers :: ", low_headers)
                return {}
                # return {'barcode_term_import_err': 'Wrong data format: table should contain external identifier in column ' + file_columns[3]}
            ext_id_for_new_doc = preview.pop(1)[ext_id_pos]
            already_imported_id_num = self.env['barcode_terminal.barcode_collection'].search_count(
                [('ext_id', '=like', ext_id_for_new_doc)], limit=1)
            if already_imported_id_num > 0:
                print("This job already imported")
                return {}
                # return {'barcode_term_import_err' : 'This job already imported'}
        else:
            print("NO --- OPTIONS.get('has_headers') and preview:")
            return {}
            # header_types, headers = {}, []
        c = len(file_columns)
        f = len(model_fields)
        n = min(c, f)
        file_columns = file_columns[:n]
        model_fields = model_fields[:n]

        file_columns = [col.lower() for col in file_columns]

        # print(headers)
        if not low_headers == file_columns:
            mappingDict = dict(map(lambda i, j: (i.lower(), j), file_columns, model_fields))
            new_model_fields = []
            new_file_columns = []
            print('mappingDict :::: ', mappingDict)
            for file_col in low_headers:
                new_model_field = mappingDict.get(file_col, False)
                new_file_columns.append(file_col)
                new_model_fields.append(new_model_field)
            model_fields = new_model_fields
            file_columns = new_file_columns

        try:
            input_file_data, import_fields = import_wizard._convert_import_data(model_fields, OPTIONS)
            # print('model_fields ', model_fields)
            # print('import_fields ', import_fields)
            # Parse date and float field
            input_file_data = import_wizard._parse_import_data(input_file_data, import_fields, OPTIONS)
        except import_wizard.ImportValidationError as error:
            # print('fail after _convert_import_data, _parse_import_data', [error.__dict__])
            return {}
            # return {'messages': [error.__dict__]}

        # _logger.info('importing %d rows...', len(input_file_data))
        import_fields, merged_data = import_wizard._handle_multi_mapping(import_fields, input_file_data)

        custom_values = {}
        # fields_cnt = len(import_fields)
        line_ids = []
        for val_list in merged_data:
            new_line_values = {}
            for i, field_name in enumerate(import_fields):
                if field_name.startswith('line_ids/'):
                    new_line_values[field_name[9:]] = val_list[i]
                else: custom_values[field_name] = val_list[i]
            line_ids.append(fields.Command.create(new_line_values))
        # print('custom_values: ', custom_values)
        custom_values['line_ids'] = line_ids
        # print('custom_values_2: ', custom_values)
        return custom_values

    def _create_import_record_with_data(self, res_model, file_name, data):
        """Create and return a ``base_import.import`` record."""
        file_ext = file_name.rsplit(".",1)[1]
        file_type = ""
        if(file_ext.lower() == "csv"):
            file_type = 'text/csv'
        elif(file_ext.lower() == "xls"):
            file_type = 'application/vnd.ms-excel'
        elif(file_ext.lower() == "xlsx"):
            file_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

        return self.env["base_import.import"].create(
            {
                "res_model": res_model,
                "file": data,
                "file_name": file_name,
                "file_type": file_type,
            }
        )


