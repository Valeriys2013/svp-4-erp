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
import io
import os
from zipfile import ZipFile

from odoo import fields, models, api, exceptions
from odoo.exceptions import UserError


class ImportZipDialog(models.TransientModel):
    _name = 'barcode_terminal.import_zip_dialog'
    _description = 'Upload File Dialog (zip, csv, xls)'

    loaded_filename = fields.Char()
    loaded_file = fields.Binary(string="Upload ZIP; CSV; XLS", help='Zip files from Android app "SVP Barcode Collector"')

    model_fields = ['name', False, 'start_timestamp', 'id', 'collection_comment', 'line_ids/barcode', 'line_ids/barcode_name',
                    'line_ids/quantity', 'line_ids/barcode_comment', False, False, 'line_ids/image_1920', 'line_ids/price_unit']
    file_columns = ['taskname', 'rowcnt', 'starttime', 'endtime', 'taskcomment', 'code', 'name',
                    'quantity', 'comment', 'format', 'picturefile', 'b64picture', 'cost']
    file_columns_adapted = ['collection', 'rowcnt', 'starttime', 'version', 'collectioncomment', 'barcode', 'name',
                            'counted quantity', 'description', 'format', 'picturefile', 'image', 'cost']

    @api.model
    def view_init(self, fields_list):
        """ Override this method to do specific things when a form view is
        opened. This method is invoked by :meth:`~default_get`.
        """
        pass

    @api.onchange("loaded_file")
    def _onchange_zip_file(self):
        print("_onchange_zip_file()>>self.loaded_filename : ", self.loaded_filename)
        return {'type': 'ir.actions.act_window_close'}


    def import_zip_cvs_xls_files(self):
        if not self.loaded_file:
            return
        # import base64
        decoded_b64_data = base64.decodebytes(self.loaded_file)
        err_list = ""
        loaded_filename = self.loaded_filename

        self.import_raw_zip_csv_xls_file(decoded_b64_data, loaded_filename)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def import_raw_zip_csv_xls_file(self, decoded_b64_data, loaded_filename):
        tmp = loaded_filename.split('.')
        ext = tmp[len(tmp) - 1]
        if ext == 'zip':
            buffer = io.BytesIO(decoded_b64_data)
            zip_data = ZipFile(buffer)
            name_list = zip_data.namelist()
            # data_file_name = name_list[0]
            for data_file_name in name_list:
                tmp = data_file_name.split('.')
                data_f_ext = tmp[len(tmp) - 1]
                if data_f_ext == 'csv' or data_f_ext == 'xls':
                    data = zip_data.open(data_file_name)
                    data_b64 = base64.encodebytes(data.read())
                    # print("_import_zip_cvs_xls_files try zip : ")
                    err_list = self.barcode_term_import(data_b64, data_file_name)
                    if 'messages' in err_list:
                        if err_list['messages']:
                            print("_import_zip_cvs_xls_files ZIP >> barcode_term_import errors : ", err_list)
                            msg = self.get_import_errors_string(err_list)
                            raise UserError("Errors while importing barcode terminal data : \n" + msg)
                        else:
                            print("ok!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                    # else:
                    #     return self.show_notification(err_list)
                else:
                    continue

        elif ext == 'csv' or ext == 'xls':
            print('_import_zip_cvs_xls_files try : ')
            err_list = self.barcode_term_import(self.loaded_file, loaded_filename)
            if 'messages' in err_list:
                if err_list['messages']:
                    print("_import_zip_cvs_xls_files >> barcode_term_import errors : ", err_list)
                    msg = self.get_import_errors_string(err_list)
                    raise UserError("Errors while importing barcode terminal data : \n" + msg)
                else:
                    print("ok!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        else:
            pass

    # def show_notification(self, err_list):
    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'title': 'Input file format error',
    #             'type': 'warning',
    #             'message': err_list['barcode_term_import_err'],
    #             'sticky': True
    #         }
    #     }

    def get_import_errors_string(self, err_list):
        msg = ''
        for d in err_list['messages']:
            msg += d['message']
            if d['record']:
                msg += 'for (' + str(d['record']) + ')'
            msg += '\n'
        print('msg ===== ', msg)
        return msg

    def barcode_term_import(self, data_file, data_file_name):
        b64_data = base64.decodebytes(data_file)

        first_try_errors = self.try_exec_import("barcode_terminal.barcode_collection", b64_data, data_file_name,
                                    self.model_fields, self.file_columns)
        if not 'barcode_term_import_err' in first_try_errors:
            print(first_try_errors)
            return first_try_errors
        second_try_errors = self.try_exec_import("barcode_terminal.barcode_collection", b64_data, data_file_name,
                                           self.model_fields, self.file_columns_adapted)
        if not 'barcode_term_import_err' in second_try_errors:
            return second_try_errors
        raise UserError(second_try_errors['barcode_term_import_err'])
        # return second_try_errors

    def try_exec_import(self, res_model, data_file, data_file_name, model_fields, file_columns):

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
                return {
                    'barcode_term_import_err': 'Wrong data format: table should contain external identifier in column ' +
                                               file_columns[3]}

            ext_id_for_new_doc = preview.pop(1)[ext_id_pos]

            already_imported_id_num = self.env['barcode_terminal.barcode_collection'].search_count(
                [('ext_id', '=like', ext_id_for_new_doc)], limit=1)
            if already_imported_id_num > 0:
                raise UserError("This job already imported")
                # return {'barcode_term_import_err' : 'This job already imported'}
        else:
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
            # mappingDict = dict(zip(file_columns, model_fields))
            mappingDict = dict(map(lambda i, j: (i.lower(), j), file_columns, model_fields))
            new_model_fields = []
            new_file_columns = []
            # print('mappingDict :::: ', mappingDict)
            for file_col in low_headers:
                new_model_field = mappingDict.get(file_col, False)
                new_file_columns.append(file_col)
                new_model_fields.append(new_model_field)
            model_fields = new_model_fields
            file_columns = new_file_columns

        return import_wizard.execute_import(model_fields, file_columns, OPTIONS)



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

    def _create_import_record(self, res_model, file_p_name):
        file_name = os.path.basename(file_p_name)

        file_ext = file_name.rsplit(".",1)[1]
        file_type = ""
        if(file_ext.lower() == "csv"):
            file_type = 'text/csv'
        elif(file_ext.lower() == "xls"):
            file_type = 'application/vnd.ms-excel'
        elif(file_ext.lower() == "xlsx"):
            file_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'

        with open(file_p_name) as data_file:
            return self.env["base_import.import"].create(
                {
                    "res_model": res_model,
                    "file": data_file.read(),
                    "file_name": file_name,
                    "file_type": file_type,
                }
            )




