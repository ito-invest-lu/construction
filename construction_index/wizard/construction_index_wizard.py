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

class ConstructionIndexWizard(models.TransientModel):
    _name = "construction.index_wizard"

    new_index = fields.Float(string="New Index")

    sale_order_ids = fields.Many2many('sale.order', 'sale_order_index_wizard_rel', 'wizard_id', 'sale_order_id',
                                      string='Sales Orders', copy=False, readonly=True)

    @api.model
    def default_get(self, fields):
        res = super(ConstructionIndexWizard, self).default_get(fields)
        res['sale_order_ids'] = self._context.get('active_ids') or self._context.get('active_id')
        return res

    @api.one
    def action_confirm(self) :
        return self.sale_order_ids.update_index(self.new_index)
