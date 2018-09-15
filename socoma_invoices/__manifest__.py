# -*- encoding: utf-8 -*-
# see LICENSE file

{
    'name': 'Socoma Custom Invoices',
    'version': '0.1',
    'category': 'Accounting',
    'description': """
    Customisation des factures pour Socoma.
    """,
    "author": "be-cloud.be (Jerome Sonnet)",
    "website": "http://www.be-cloud.be",
    'depends': ['account'],
    'init_xml': [],
    'data': [
        'views/construction_invoice_view.xml',
    ],
    'installable': True,
    'active': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: