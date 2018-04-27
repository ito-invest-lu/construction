# -*- encoding: utf-8 -*-
# see LICENSE file

{
    'name': 'Construction Forecast',
    'version': '0.1',
    'category': 'Sales',
    'description': """
    Create Kanban view to forecast sale order.
    """,
    "author": "be-cloud.be (Jerome Sonnet)",
    "website": "http://www.be-cloud.be",
    'depends': ['construction'],
    'init_xml': [],
    'data': [
        'views/construction_forecast_view.xml',
    ],
    'installable': True,
    'active': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: