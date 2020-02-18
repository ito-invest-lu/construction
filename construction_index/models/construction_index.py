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
    current_index = fields.Float(string="Current Index", readonly=True)

    @api.one
    def update_index(self, index):
        self.current_index = index
        self.order_line.filtered(lambda line : line.qty_invoiced < line.product_uom_qty)._update_index()

    @api.onchange('is_indexed')
    def onchange_is_indexed(self):
        self.order_line.reset_initial_price_unit()

    @api.multi
    def write(self, vals):
        if 'initial_index' in vals :
            vals['current_index'] = vals['initial_index']
        return super(SaleOrder, self).write(vals)

class SaleOrderLine(models.Model):
    '''Sale Order Line'''
    _inherit = "sale.order.line"

    initial_price_unit = fields.Float('Initial Unit Price', required=True, digits=dp.get_precision('Product Price'), default=0.0)

    @api.multi
    def reset_initial_price_unit(self):
        for line in self:
            line.initial_price_unit = line.price_unit

    @api.onchange('price_unit')
    def _onchange_unit_price(self):
        if self.state == 'draft' :
            self.initial_price_unit = self.price_unit

    @api.multi
    def _update_index(self):
        for line in self :
            if line.initial_price_unit == 0 :
                raise UserError('Initial Price not set, cannot use index')
            line.price_unit = line.initial_price_unit * line.order_id.current_index / line.order_id.initial_index
