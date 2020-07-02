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

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

import odoo.addons.decimal_precision as dp

_logger = logging.getLogger(__name__)

class SignRequest(models.Model):
    _name = 'website_sign.request'
    _inherit = ['website_sign.request', 'documents.mixin']

    sale_order_id = fields.Many2one(related='template_id.sale_order_id', readonly=True)

class SignTemplate(models.Model):
    _name = 'website_sign.template'
    _inherit = ['website_sign.template', 'documents.mixin']

    sale_order_id = fields.Many2one('sale.order', 'Signed Sale Order')

class SaleOrder(models.Model):
    '''Sale Order'''
    _inherit = "sale.order"

    upload_order_details = fields.Binary(string="Upload Order Details", attachment=True)
    order_details_file_name = fields.Char(string="Order Details File Name")
    
    order_details_sign_request_ids = fields.One2many('website_sign.request', 'sale_order_id', string="Sign requests")
    order_details_sign_request_count = fields.Integer(compute='_compute_sign_request_count', string='Sign requests Count')
    
    @api.depends('order_details_sign_request_ids')
    def _compute_mailing_mail_count(self):
        for so in self:
            so.order_details_sign_request_count = len(so.order_details_sign_request_ids)
    
    @api.multi
    def sign_sale_order_details(self):
        
        if not upload_order_details :
            raise UserError('Vous devez d''abords uploader le détail du devis')
        
        create_values = {
            'name': this.name + '-' + this.partner_id.name,
            'attachment_id': self.upload_order_details.id,
            'favorited_ids': [(4, self.env.user.id)],
        }

        new_obj = self.env['website_sign.template'].create(create_values)
        
        action = {
            'type': 'ir.actions.act_window',
            'res_model': 'website_sign.template',
            'name': _("New templates"),
            'view_id': False,
            'view_mode': 'form',
            'views': [(False, "kanban"), (False, "form")],
            'domain': [('id', '=', new_obj.id)],
            'context': self._context,
        }
        