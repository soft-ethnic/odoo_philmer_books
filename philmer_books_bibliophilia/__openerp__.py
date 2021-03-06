# -*- coding: utf-8 -*-
{
    'name': u"Import of Bibliophilia backups files into Philmer's Books",
    'summary': "BiblioPhilia is perfect on iPhone to get quick data about books.\nPhilmer's Books is perfect to manage my library.\nThis module links them ...",
    'description':"""
This module permit the import of biblioPhilia backup files into Philmer's Books.\nManage the import of the same backup again and again.\nManage the link betweek Philmer's books and Bibliophilia's records'
""",
    'depends': ['base','philmer_books'],
    'data': ['security/ir.model.access.csv',
             'views/philmer_books_imported_ids_view.xml',
             'views/wizard_import_bibliophilia.xml',],
    'version':'1.0',
    'application':False,
    'installable': True,
    'auto_install': False,
}
