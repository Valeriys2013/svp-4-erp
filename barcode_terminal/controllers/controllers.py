# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


# class BarcodeTerminal(http.Controller):
#     @http.route('/barcode_terminal/barcode_collection/control_new_implementations', type='json', auth='public')
#     def control_find_new_implementations(self, domain, **kw):
#         Collections = request.env['barcode_terminal.barcode_collection']
#         return Collections.find_new_implementations(domain)
#
#     @http.route('/barcode_terminal/barcode_collection/control_model_fun_for_rpc', type='json', auth='public')
#     def control_model_fun_for_rpc(self, domain,**kw):
#         Collections = request.env['barcode_terminal.barcode_collection']
#         return Collections.model_fun_for_rpc(domain)
#         # return "Hello, world"
#
#
#     @http.route('/barcode_terminal/barcode_collection', type='json', auth='public')
#     def index(self, **kw):
#         return "Hello, world"
#
#     @http.route('/barcode_terminal/barcode_collection/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('barcode_terminal.listing', {
#             'root': '/barcode_terminal/barcode_terminal',
#             'objects': http.request.env['barcode_terminal.barcode_collection'].search([]),
#         })
#
#     @http.route('/barcode_terminal/barcode_collection/objects/<model("barcode_terminal.barcode_collection"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('barcode_terminal.object', {
#             'object': obj
#         })
