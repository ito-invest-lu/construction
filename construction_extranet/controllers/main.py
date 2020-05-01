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
    
    @http.route('/invoices/<int:company_id>', type='http', auth='none', csrf=False)
    def invoices(self, company_id, debug=False, **k):
        values = {
            'company_id': request.env['res.company'].browse(company_id),
            'draft_invoice_ids' : request.env['account.move'].sudo().search([('company_id','=',company_id),('state','=','draft')]),
            'open_invoice_ids' : request.env['account.move'].sudo().search([('company_id','=',company_id),('state','=','open')]),
            'paid_invoice_ids' : request.env['account.move'].sudo().search([('company_id','=',company_id),('state','=','paid')]),
        }
        return request.render('construction_extranet.invoices', values)