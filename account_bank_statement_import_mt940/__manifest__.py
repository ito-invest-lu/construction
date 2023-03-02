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
{
    'name': 'Import MT940 Bank Statement',
    'category' : 'Accounting & Finance',
    'version': '0.1',
    'author': 'be-cloud.be (Jerome Sonnet)',
    'description' : """
Module to import MT940 bank statements.
======================================

This module allows you to import MT940 files in Odoo: they are parsed and stored in human readable format in
Accounting \ Bank and Cash \ Bank Statements.

    """,
    'data': [],
    'depends': ['account_bank_statement_import'],
    'demo': [],
    'external_dependencies': {
        'python': ['mt-940'],
    },
    'auto_install': False,
    'installable': True,
}
