# -*- encoding: utf-8 -*-
# see LICENSE file

{
    'name': 'Construction Extranet',
    'version': '0.1',
    'category': 'Accounting',
    'description': """
    Extranet pour consulter le niveau des factures.
    """,
    "author": "be-cloud.be (Jerome Sonnet)",
    "website": "http://www.be-cloud.be",
    'depends': ['account'],
    'init_xml': [],
    'data': [
        'views/construction_extranet_view.xml',
    ],
    'installable': True,
    'active': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: