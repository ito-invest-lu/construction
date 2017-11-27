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

class CRMLead(models.Model):
    _inherit = 'crm.lead'
    
    # Method to called by CRON to update colors
    @api.model
    def recompute_all(self):
        leads = self.search([('active', '=', True)])
        leads._update_color()
        return True
    
    @api.one
    def _update_color(self):
        if self.write_date < datetime.now()-timedelta(days=10) :
            self.color = 9    
        elif self.write_date < datetime.now()-timedelta(days=3) :
            self.color = 2
        else :
            self.color = 10