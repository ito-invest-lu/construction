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

class ConstructionForecastWizard(models.TransientModel):
    _name = "construction.forecast_wizard"
    
    order_line_ids = fields.One2many('sale.order.line', 'forecast_month_id', string='Lines')
    forecast_month_id = fields.Many2one('sale.order.line.forecast_month', string='Assigned to Month')
    
    @api.multi
    def action_confirm(self):
        self.ensure_one()
        self.order_line_ids.write({
            'forecast_month_id' : self.forecast_month_id
        })