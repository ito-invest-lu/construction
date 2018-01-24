# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (c) 2010-2017 Be-Cloud.be All Rights Reserved.
#
#    Author: Jerome Sonnet <jerome.sonnet@be-cloud.be>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import logging
import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import email_split, float_is_zero

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """ Overrides mail_thread message_new that is called by the mailgateway
            through message_process.
            This override updates the document according to the email.
        """
        self = self.with_context(default_user_id=False)

        if custom_values is None:
            custom_values = {}
            
        partner_id = msg_dict.get('author_id', False)
        defaults = {
            'name': 'Nouveau',
            'partner_id': partner_id,
            'partner_invoice_id': partner_id,
            'partner_shipping_id': partner_id,
            'user_id': partner_id,
            'order_line': [(0, 0, {
                'name': 'Suppléments',
                'product_id': 13,
                'product_uom_qty': 1,
                'price_unit': 100.00,
            })],
        }
        
        defaults.update(custom_values)
        return super(SaleOrder, self).message_new(msg_dict, custom_values=defaults)
        
        