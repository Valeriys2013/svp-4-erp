# -*- coding: utf-8 -*-
# from odoo import http


# class BarcodeTerminal(http.Controller):
#     @http.route('/barcode_terminal/barcode_terminal', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/barcode_terminal/barcode_terminal/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('barcode_terminal.listing', {
#             'root': '/barcode_terminal/barcode_terminal',
#             'objects': http.request.env['barcode_terminal.barcode_terminal'].search([]),
#         })

#     @http.route('/barcode_terminal/barcode_terminal/objects/<model("barcode_terminal.barcode_terminal"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('barcode_terminal.object', {
#             'object': obj
#         })
