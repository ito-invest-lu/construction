# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (c) 2010-2012 Be-Cloud.be All Rights Reserved.
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
        
        # We change the route of message if the subject match the pattern "#xx"
        # to the existing ticket "#xx".
        ticket_description = msg_dict.get('subject', '')

        # Match the first occurence of '#(d+)' in the string and extract 
        # the ticket number to send the message to.
        pattern = '#(\d+)'
        match = re.search(pattern, ticket_description)
        if match is None:
            # No match we continue the currrent behavior
            ticket = super(HelpdeskTicket, self).message_new(msg_dict, custom_values)
            all_emails = ticket._ticket_email_split(msg_dict)
            try:
                _logger.info("Look for emails in %s" % msg_dict.get('body', ''))
                all_emails = list(set(all_emails + re.findall('[a-zA-Z0-9+._-]+@[a-zA-Z0-9._-]+\.[a-zA-Z0-9_-]+',msg_dict.get('body', ''))))
                _logger.info("Found emails %s" % all_emails)
            except:
                _logger.info("Cannot find all emails in %s" % msg_dict.get('body', ''))
                pass
            alias_domain = self.env["ir.config_parameter"].sudo().get_param("mail.catchall.domain")
            foreign_emails = [x for x in all_emails if alias_domain not in x]
            partner_id = False
            for parsed_email in foreign_emails:
                partner_id = self.search([('email', '=ilike', parsed_email)], limit=1)
                if partner_id:
                    break
            if partner_id :
                _logger.info("Ticket customer set to %s" % partner_id.name)
                ticket.partner_id = partner_id
                ticket.partner_email = partner_id.email
            else :
                _logger.info("No customer found for %s leave to %s" % (foreign_emails, ticket.partner_id.name if ticket.partner_id else 'None'))
            return ticket
        else:
            # We have a match we switch to message_update
            ticket_id = self.env['helpdesk.ticket'].browse(int(match.group(1)))
            _logger.info("Ticket number found in subject, message rerouted to ticket #%s" % ticket_id.id)
            new_msg = ticket_id.message_post(subtype='mail.mt_comment', **msg_dict)
            return ticket_id.id