# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2015 be-cloud.be
#                       Jerome Sonnet <jerome.sonnet@be-cloud.be>
#
#    Thanks to Alexis Yushin <AYUSHIN@thy.com> for sharing code/ideas
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

from odoo import models

import mt940
import logging

import base64
import io

_logger = logging.getLogger(__name__)

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    def _get_bank_statements_available_import_formats(self):
        rslt = super()._get_bank_statements_available_import_formats()
        rslt.append('MT940')
        return rslt
    
    def _parse_bank_statement_file(self,attachment):
        
        currency = None
        account = None
        statements = []
        
        try:
            transactions = mt940.parse(io.BytesIO(attachment.raw))
            # if no statements found
            if not transactions:
                _logger.debug("Statement file was not recognized as an MT940 file, trying next parser", exc_info=True)
                return super()._parse_bank_statement_file(attachment)
            
            statement = {
                'balance_start': transactions.data['final_opening_balance'].amount.amount,
                'balance_end_real': transactions.data['final_closing_balance'].amount.amount,
                'transactions' : [],
            }
            
            currency = transactions.data['final_opening_balance'].amount.currency
            account = transactions.data['account_identification'].split('/')[1]
            
            # we iterate through each transaction
            for t in transactions:
                st_line = {
                    'date' : t.data.get('entry_date') or t.data.get('date'),    
                    'amount' : t.data['amount'].amount,
                    'payment_ref' : t.data.get('additional_purpose') or t.data.get('extra_details') or t.data.get('bank_reference'),
                    'sequence': len(statement['transactions']) + 1,
                }
                statement['transactions'].append(st_line)
            
            return currency, account, [statement]
                    
        except Exception as e:
            _logger.info(e)
            return super()._parse_bank_statement_file(attachment)