# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2015 be-cloud.be
#                       Jerome Sonnet <jerome.sonnet@be-cloud.be>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import base64
import json
import logging
import werkzeug
import math

from odoo import http, tools, _
from odoo.addons.http_routing.models.ir_http import slug
from odoo.exceptions import AccessError, UserError
from odoo.http import request
from odoo.osv import expression

_logger = logging.getLogger(__name__)

class ConstructionController(http.Controller):
    
    @http.route('/invoice_supplier/<int:company_id>', type='http', auth='none', csrf=False)
    def invoices_supp(self, company_id, debug=False, **k):
        values = {
            'company_id': request.env['res.company'].browse(company_id),
            'draft_invoice_ids' : request.env['account.move'].sudo().search([('company_id','=',company_id),('state','=','draft'),('type', '=', 'in_invoice')]),
            'open_invoice_ids' : request.env['account.move'].sudo().search([('company_id','=',company_id),('state','=','posted'),('amount_residual','!=','0'),('type', '=', 'in_invoice')]),
            'paid_invoice_ids' : request.env['account.move'].sudo().search([('company_id','=',company_id),('state','=','posted'),('amount_residual','=','0'),('type', '=', 'in_invoice')]),
        }
        return request.render('construction_extranet.invoices', values)
        
    @http.route('/invoice_customer/<int:company_id>', type='http', auth='none', csrf=False)
    def invoices_cust(self, company_id, debug=False, **k):
        values = {
            'company_id': request.env['res.company'].browse(company_id),
            'draft_invoice_ids' : request.env['account.move'].sudo().search([('company_id','=',company_id),('state','=','draft'),('type', '=', 'out_invoice')], order="partner_id, date desc"),
            'open_invoice_ids' : request.env['account.move'].sudo().search([('company_id','=',company_id),('state','=','posted'),('amount_residual','!=','0'),('type', '=', 'out_invoice')], order="partner_id, date desc"),
            'paid_invoice_ids' : request.env['account.move'].sudo().search([('company_id','=',company_id),('state','=','posted'),('amount_residual','=','0'),('type', '=', 'out_invoice')], order="partner_id, date desc"),
        }
        return request.render('construction_extranet.invoices', values)
        
    @http.route('/invoice_analytics/<int:company_id>', type='http', auth='none', csrf=False)
    def invoices_analytics(self, company_id, debug=False, **k):
        
        analytic_account_ids = request.env['account.analytic.account'].sudo().search([('company_id','=',company_id)])
        
        values = {
            'company_id': request.env['res.company'].browse(company_id),
            'analytics': [],
        }
        
        for analytic_account in analytic_account_ids:
            analytic = {
                'id' : analytic_account.id,
                'name' : analytic_account.name,
                'partners': [],
            }
            groups = request.env['account.move'].sudo().read_group(
                [["type", "=", "in_invoice"], ["invoice_line_ids.analytic_account_id.id", "=", analytic_account.id]],
                [],
                ['partner_id']
            )
            for partner_group in  groups:
                partner = {
                    'id': partner_group.get('partner_id')[0],
                    'name': request.env['res.partner'].sudo().browse(partner_group.get('partner_id')[0]).name, # REALLY ??
                    'invoices' : request.env['account.move'].sudo().search(partner_group.get('__domain'))
                }
                analytic['partners'].append(partner)
            values['analytics'].append(analytic)
        return request.render('construction_extranet.invoices_analytics', values)
        
        
    @http.route('/invoice_original/<int:invoice_id>', type='http', auth='none', csrf=False)
    def invoices_original(self, invoice_id, debug=False, **k):
        invoice = request.env['account.move'].sudo().browse(invoice_id), 
        if invoice :
            return werkzeug.utils.redirect('/web/content/%s' % invoice[0].message_main_attachment_id.id)
            
    
    @http.route('/purchase_orders/<int:company_id>', type='http', auth='none', csrf=False)
    def purchase_orders(self, company_id, debug=False, **k):
        values = {
            'company_id': request.env['res.company'].browse(company_id),
            'draft_invoice_ids' : request.env['account.move'].sudo().search([('company_id','=',company_id),('state','=','draft'),('type', '=', 'out_invoice')]),
            'open_invoice_ids' : request.env['account.move'].sudo().search([('company_id','=',company_id),('state','=','posted'),('amount_residual','!=','0'),('type', '=', 'out_invoice')]),
            'paid_invoice_ids' : request.env['account.move'].sudo().search([('company_id','=',company_id),('state','=','posted'),('amount_residual','=','0'),('type', '=', 'out_invoice')]),
        }
        return request.render('construction_extranet.invoices', values)