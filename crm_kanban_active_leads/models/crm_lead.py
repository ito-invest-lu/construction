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
from odoo.exceptions import UserError

from datetime import timedelta, datetime

_logger = logging.getLogger(__name__)

IMPORTANT_FIELDS = ['name','priority','state_id','kanban_state','probability','sale_amount_total','stage_id','message_ids']

class CRMLead(models.Model):
    _inherit = 'crm.lead'
    
    last_modification_for_followup = fields.Datetime('Last Modification for Followup', default=fields.Datetime.now())
    
    @api.multi
    def write(self, values):
        sync_fields = set(self.get_fields_need_update_google())
        if set(values) and IMPORTANT_FIELDS :
            values['last_modification_for_followup'] = fields.Datetime.now()
        return super(CRMLead, self).write(values)
    
    # Method to called by CRON to update colors
    @api.model
    def recompute_all(self):
        leads = self.search([('active', '=', True)])
        leads._update_color()
        return True
    
    @api.one
    def _update_color(self):
        w_date = fields.Datetime.from_string(self.last_modification_for_followup)
        if  w_date< datetime.now()-timedelta(days=10) :
            self.color = 9    
        elif w_date < datetime.now()-timedelta(days=3) :
            self.color = 2
        else :
            self.color = 10