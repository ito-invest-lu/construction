# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (c) 2010-2012 Elico Corp. All Rights Reserved.
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


class HelpdeskTicket(models.Model):
    _inherit = 'helpdesk.ticket'
    
    @api.model
    def message_new(self, msg_dict, custom_values=None):
        if custom_values is None:
            custom_values = {}

        email_address = email_split(msg_dict.get('email_from', False))[0]

        employee = self.env['hr.employee'].search([
            '|',
            ('work_email', 'ilike', email_address),
            ('user_id.email', 'ilike', email_address)
        ], limit=1)

        ticket_description = msg_dict.get('subject', '')

        # Match the first occurence of '#(d+)' in the string and extract 
        # the ticket number to send the message to.
        pattern = '#(\d+)'
        match = re.search(pattern, ticket_description)
        if match is None:
            super(HelpdeskTicket, self).message_new(msg_dict, custom_values)
        else:
            ticket_id = self.env['helpdesk.ticket'].browse(match.group(1))[0]
            _logger.info("Message routed to ticket #%s" % ticket_id.id)
            ticket_id.message_update(msg_dict)