# -*- encoding: utf-8 -*-
# see LICENSE file

{
    'name': 'Construction Porjects',
    'version': '0.1',
    'category': 'Project',
    'description': """
        Integrates building assets with projects.
    """,
    "author": "be-cloud.be (Jerome Sonnet)",
    "website": "http://www.be-cloud.be",
    'depends': ['construction','project'],
    'init_xml': [],
    'data': [
        'data/task_type_definition.xml',
        'views/construction_project_view.xml',
        'wizard/construction_project_wizard.xml',
    ],
    'installable': True,
    'active': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: