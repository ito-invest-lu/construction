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

from lxml import html

from openerp import api, fields, models, _
from openerp.exceptions import UserError

_logger = logging.getLogger(__name__)

class CrmLead(models.Model):
    '''Building Site'''
    _inherit = 'crm.lead'
    
    @api.one
    def parse_message(self):
        for message in self.message_ids:
            if message.body:
                body = html.fromstring(message.body)
                node = body.xpath("//td[text() = 'Nom :']/following-sibling::td")
                self.name = node[0].text
                node = body.xpath("//td[text() = 'Email :']/following-sibling::td")
                self.email_from = node[0].text
                node = body.xpath("//td[text() = 'Téléphone :']/following-sibling::td")
                self.phone = node[0].text
        self.tag_ids = [(4, 1)] # athome tag ;-)