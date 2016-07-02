# -*- coding: utf-8 -*-
{
    'name': u"Books Management for Philmer and Family",
    'summary': "Manage books, magazines etc of the Philmer's family",
    'description':"""
Manage books, magazines etc of the Philmer's family
""",
    'depends': ['base',],
    'data': ['views/philmer_books_view.xml',
             'views/philmer_book_reading.xml',
             'views/res_partner.xml',
             'views/res_users.xml',
             'report/menu_report.xml',
             'report/philmer_book_catalog.xml',
            ],
    'version':'1.0',
    'application':True,
    'installable': True,
    'auto_install': False,
}
