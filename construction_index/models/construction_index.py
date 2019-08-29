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

class SaleOrder(models.Model):
    '''Sale Order'''
    _inherit = "sale.order"

    is_indexed = fields.Boolean(string="Is Indexed")

    initial_index = fields.Float(string="Initial Index", readonly=True, states={'draft': [('readonly', False)]})
    current_index = fields.Float(string="Current Index")

    @api.onchange('initial_index')
    def _onchange_initial_index(self):
        self.current_index = self.initial_index

class SaleOrderLine(models.Model):
    '''Sale Order Line'''
    _inherit = "sale.order.line"

    initial_price_unit = fields.Float('Initial Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0, readonly=True)

    @api.depends('price_unit')
    def _setup_initial_price(self):
        if state == 'draft' :
            for line in self:
                line.initial_price_unit = line.price_unit

    @api.depends('order_id.current_index')
    def _update_index(self):
        for line in self :
            line.price_unit = line.initial_price_unit * order_id.current_index / order_id.initial_index
