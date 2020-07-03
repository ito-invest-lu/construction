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
import logging

import re
import base64

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

import odoo.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)

class SignRequest(models.Model):
    _name = 'signature.request'
    _inherit = ['signature.request']

    sale_order_id = fields.Many2one(related='template_id.sale_order_id', readonly=True)

class SignTemplate(models.Model):
    _name = 'signature.request.template'
    _inherit = ['signature.request.template']

    sale_order_id = fields.Many2one('sale.order', 'Signed Sale Order')

class SaleOrder(models.Model):
    '''Sale Order'''
    _inherit = "sale.order"

    upload_order_details = fields.Binary(string="Upload Order Details", attachment=True)
    order_details_file_name = fields.Char(string="Order Details File Name")
    
    order_details_sign_request_ids = fields.One2many('signature.request', 'sale_order_id', string="Sign requests")
    order_details_sign_request_count = fields.Integer(compute='_compute_sign_request_count', string='Sign requests Count')
    
    @api.depends('order_details_sign_request_ids')
    def _compute_sign_request_count(self):
        for so in self:
            so.order_details_sign_request_count = len(so.order_details_sign_request_ids)
    
    def _count_pages_pdf(self, bin_pdf):
        """ Count the number of pages of the given pdf file.
            :param bin_pdf : binary content of the pdf file
        """
        pages = 0
        for match in re.compile(b"/Count\s+(\d+)").finditer(bin_pdf):
            pages = int(match.group(1))
        return pages
    
    @api.multi
    def sign_sale_order_details(self):
        
        if not self.upload_order_details :
            raise UserError('Vous devez d''abords uploader le détail du devis')
        
        attachment = self.env["ir.attachment"].search([('res_model', '=', 'sale.order'), ('res_field', '=', 'upload_order_details'), ('res_id', '=', self.id)])

        # Fix attachment name and datas_fname for signature
        attachment.write({
            'name' : self.name + '-' + self.partner_id.name ,
            'datas_fname': self.order_details_file_name
        })
        
        pages = self._count_pages_pdf(base64.b64decode(attachment.datas))
        
        create_signature_items_value = [(0,_,{
            'name'      : "signature",
            'page'      : pages,
            'height'    : 0.05,
            'width'     : 0.2,
            'posX'      : 0.288,
            'posY'      : 0.881,
            'type_id'   : self.env.ref('website_sign.signature_item_type_signature').id,
            'required'  : True,
            'responsible_id' : self.env.ref('website_sign.signature_item_party_customer').id,
        }),(0,_,{
            'name'      : "date",
            'page'      : pages,
            'height'    : 0.015,
            'width'     : 0.15,
            'posX'      : 0.288,
            'posY'      : 0.854,
            'type_id'   : self.env.ref('website_sign.signature_item_type_date').id,
            'required'  : True,
            'responsible_id' : self.env.ref('website_sign.signature_item_party_customer').id,
        })]
        
        if pages > 1 :
            for p in range(pages-1):
                create_signature_items_value.append(
                    (0,_,{
                        'name'      : "initiales",
                        'page'      : p+1,
                        'height'    : 0.030,
                        'width'     : 0.085,
                        'posX'      : 0.895,
                        'posY'      : 0.939,
                        'type_id'   : self.env.ref('website_sign.signature_item_type_initial').id,
                        'required'  : True,
                        'responsible_id' : self.env.ref('website_sign.signature_item_party_customer').id,
                    })
                )

        create_values = {
            'attachment_id': attachment[0].id,
            'favorited_ids': [(4, self.env.user.id)],
            'sale_order_id' : self.id,
            'signature_item_ids' : create_signature_items_value,
        }

        new_obj = self.env['signature.request.template'].create(create_values)
        
        return {
            'name': "Template \"%(name)s\"" % {'name': attachment.name},
            'type': 'ir.actions.client',
            'tag': 'website_sign.Template',
            'context': {
                'id': new_obj.id,
            },
        }
        
    def action_view_signed_order(self):
        if len(self.order_details_sign_request_ids) > 1 :
            return {
                "type": "ir.actions.act_window",
                "res_model": "signature.request",
                "views": [[self.env.ref('website_sign.signature_request_view_kanban').id, "kanban"], [False, "tree"]],
                'view_mode': 'kanban,tree',
                "domain": [('id','in',self.order_details_sign_request_ids.ids)],
                "name": "Sale Order Signature Requests",
                "context": {},
            }
        else :
            return self.order_details_sign_request_ids[0].go_to_document()