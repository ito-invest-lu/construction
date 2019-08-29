# -*- encoding: utf-8 -*-
# see LICENSE file

{
    'name': 'Construction Index Management',
    'version': '0.1',
    'category': 'Sales',
    'description': """
    Add an index on Sale Order Lines and allow global indexing of all contracts.
    """,
    "author": "be-cloud.be (Jerome Sonnet)",
    "website": "http://www.be-cloud.be",
    'depends': ['construction'],
    'init_xml': [],
    'data': [
        'views/construction_index_view.xml',
        'wizard/construction_index_wizard.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'active': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
