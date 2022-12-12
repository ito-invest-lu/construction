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


import base64
import zipfile
from io import BytesIO

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.base.models.res_bank import sanitize_account_number

_logger = logging.getLogger(__name__)

class BulkImportStatement(models.TransientModel):
    _name = "account_bulk_import_wizard.account_bulk_import_wizard"
    _description = "Bulk Import Statement"
    
    zip_file = fields.Binary(string='Bank Statement File', required=True, help='Bulk import all files in a zip...')
    
    def bulk_import_statement(self):
        self.ensure_one()
        bin_data = self.zip_file and base64.b64decode(self.zip_file) or ''
        zippedFiles = zipfile.ZipFile(BytesIO(bin_data))
        statement_line_ids_all = []
        notifications_all = []
        for filename in zippedFiles.namelist():
            try :
                data = zippedFiles.read(filename)
                data_attach = {
                    'name': filename,
                    'datas': base64.b64encode(data),
                    'res_model': 'account.bank.statement',
                    'res_id': 0,
                    'type': 'binary',  # override default_type from context, possibly meant for another model!
                }
                base_import = self.env['account.bank.statement.import'].create({
                    'attachment_ids' : [(0, 0, data_attach)],
                })
                currency_code, account_number, stmts_vals = base_import.with_context(active_id=self.ids[0])._parse_file(data)
                if account_number:
                    sanitized_account_number = sanitize_account_number(account_number)
                    journal_id = self.env['account.journal'].search([('bank_account_id.sanitized_acc_number', '=', sanitized_account_number)])
                    if journal_id:
                        ret = base_import.with_context({'journal_id' : journal_id.id}).import_file()
                        if ret['type'] == 'ir.actions.client':
                            statement_line_ids_all.extend(ret['context']['statement_line_ids'])
                            notifications_all.extend(ret['context']['notifications'])
            except UserError:
                pass
        if len(statement_line_ids_all) == 0:
            raise UserError(_('You have already imported all these files.'))
        # Finally dispatch to reconciliation interface
        return {
            'type': 'ir.actions.client',
            'tag': 'bank_statement_reconciliation_view',
            'context': {'statement_line_ids': statement_line_ids_all,
                        'company_ids': self.env.user.company_ids.ids,
                        'notifications': notifications_all,
            },
        }