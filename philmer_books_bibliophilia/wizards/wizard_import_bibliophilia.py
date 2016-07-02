# -*- encoding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import Warning
import csv
import io
import base64
import logging
import os
import StringIO
import zipfile

_logger = logging.getLogger(__name__)

def _search_or_create_author(author_obj,bib_author_name):
    complete_name = bib_author_name.strip()
    if complete_name.count(' ') == 1:
        (first,last) = complete_name.split(' ')
        author_ids = author_obj.search([('last_name','=',last),('first_name','=',first)])
    else:
        first = ''
        last = complete_name
        author_ids = author_obj.search([('last_name','=',last)])
    if author_ids:
        if len(author_ids) == 1:
            return author_ids[0]
        else:
            return False
    else:
        new_author = author_obj.create({'first_name':first,'last_name':last})
        return new_author

def _search_or_create_editor(partner_obj,bib_editor_name):
    complete_name = bib_editor_name.strip()
    editor_ids = partner_obj.search([('name','=',complete_name)])
    if editor_ids:
        if len(editor_ids) == 1:
            return editor_ids[0]
        else:
            return False
    else:
        new_editor = partner_obj.create({'name':complete_name,'is_company':True,'function':'Editor'})
        return new_editor

class wizard_import_bibliophilia(models.TransientModel):
    _name = 'wizard_import_bibliophilia'
    finput = fields.Binary(string='Bibliophilia file',required=True)
    path = fields.Char('Covers\'s Path',help='Path to the covers folder.')
    
    @api.multi
    def import_file(self):
        for wizard in self:
            created_ids = []
            book_obj = self.env['philmer.book']
            author_obj = self.env['philmer.author']
            partner_obj = self.env['res.partner']
            participation_obj = self.env['philmer.book.participation']
            imported_id_obj = self.env['philmer.book.imported_id']
            lang_obj = self.env['res.lang']
            input_file_as_string = unicode(base64.decodestring(wizard.finput),'utf-16','ignore')
            input_data = wizard.finput
            _logger.info(input_file_as_string)
            covers_path = wizard.path
            if covers_path[-1:] != '/':
                covers_path += '/'
            _logger.info(covers_path)
            lines = input_file_as_string.split('\n')
            if len(lines) == 1:
                _logger.info('not windows end of line trying mac')
                lines = input_file_as_string.split('\r\n')
            if len(lines) == 1:
                _logger.info('not mac either, perhaps windows')
                lines = input_file_as_string.split('\r')
            # create language conversion table
            english_id = lang_obj.search([('iso_code','=','en_US')])[0].id
            french_id = lang_obj.search([('iso_code','=','fr_FR')])[0].id
            index = 0
            dHeaders = {}
            for line in lines:
                if index == 0:
                    headers = line.split(";")
                    index_header = 0
                    for header in headers:
                        dHeaders[header] = index_header
                        index_header += 1
                else:
                    fields = line.split(';')
                    new_fields = []
                    for field in fields:
                        new_field = field
                        if new_field[0:1] == u'"':
                            new_field = new_field[1:]
                        if new_field[-1:] == u'"':
                            new_field = new_field[:-1]
                        new_fields.append(new_field)
                    # verify if this record has not already been imported previously
                    already_ids = imported_id_obj.search([('source','=','Bibliophilia.Book'),('id_in_source','=',new_fields[dHeaders['id']])])
                    if not already_ids:
                        if len(new_fields) >= 30:
                            book_data = {}
                            # record the book data
                            book_data.update({'name':new_fields[dHeaders['title']]})
                            book_data.update({'sub_name':new_fields[dHeaders['subtitle']]})
                            book_data.update({'isbn':new_fields[dHeaders['isbn']]})
                            book_data.update({'pages':int(new_fields[dHeaders['pages']] or '0' )*1.0})
                            book_data.update({'description':new_fields[dHeaders['descr']]})
                            book_data.update({'book_type':'book'})
                            book_data.update({'book_format':'print'})
                            if new_fields[dHeaders['language']]:
                                if new_fields[dHeaders['language']] == u'Français':
                                    book_data.update({'language_id':french_id})
                                elif new_fields[dHeaders['language']] == u'Anglais':
                                    book_data.update({'language_id':english_id})
                            new_book = book_obj.create(book_data)
                            if new_book:
                                imported_id_obj.create({'source':'Bibliophilia.Book','id_in_source':new_fields[dHeaders['id']],'philmer_id':'philmer.book,'+str(new_book.id)})
                                created_ids.append(new_book.id)
                                _logger.info('after created_ids')
                                _logger.info(str(created_ids))
                                
                                # trying to get the cover
                                cover_file = covers_path + str(new_fields[dHeaders['id']]) + '.jpg'
                                _logger.info(cover_file)
                                if os.path.isfile(cover_file):
                                    _logger.info('cover exists')
                                    new_book.cover = base64.encodestring(open(cover_file, 'r').read())
                                else:
                                    _logger.info('not existing cover')
                                # trying to get/create the author
                                bib_author_id = new_fields[dHeaders['author_id']]
                                bib_author_name = new_fields[dHeaders['author']]
                                if bib_author_id:
                                    imported_authors = imported_id_obj.search([('source','=','Bibliophilia.Author'),('id_in_source','=',bib_author_id)])
                                    if imported_authors:
                                        _logger.info('found author id')
                                        _logger.info(imported_authors[0].philmer_id.id)
                                        participation_obj.create({'author_id':imported_authors[0].philmer_id.id,'participation_type':'author','book_id':new_book.id})
                                    else:
                                        author = _search_or_create_author(author_obj,bib_author_name)
                                        if author:
                                            participation_obj.create({'author_id':author.id,
                                                                      'participation_type':'author',
                                                                      'book_id':new_book.id})
                                            imported_id_obj.create({'source':'Bibliophilia.Author',
                                                                    'id_in_source':bib_author_id,
                                                                    'philmer_id':'philmer.author,'+str(author.id)})
                                else:
                                    if bib_author_name:
                                        author = _search_or_create_author(author_obj,bib_author_name)
                                        if author:
                                            participation_obj.create({'author_id':author.id,'participation_type':'author','book_id':new_book.id})
                                # trying to get/create the editor
                                bib_editor_id = new_fields[dHeaders['editor_id']]
                                bib_editor_name = new_fields[dHeaders['publisher']]
                                if bib_editor_id:
                                    imported_editors = imported_id_obj.search([('source','=','Bibliophilia.Editor'),('id_in_source','=',bib_editor_id)])
                                    if imported_editors:
                                        _logger.info('found editor id')
                                        _logger.info(imported_editors[0].philmer_id.id)
                                        new_book.write({'editor_id':imported_editors[0].philmer_id.id})
                                    else:
                                        editor = _search_or_create_editor(partner_obj,bib_editor_name)
                                        if editor:
                                            new_book.write({'editor_id':editor.id})
                                            imported_id_obj.create({'source':'Bibliophilia.Editor',
                                                                    'id_in_source':bib_editor_id,
                                                                    'philmer_id':'res.partner,'+str(editor.id)})
                                else:
                                    if bib_editor_name:
                                        editor = _search_or_create_editor(partner_obj,bib_editor_name)
                                        if editor:
                                            new_book.write({'editor_id':editor.id})
                index += 1
                _logger.info('index')
                _logger.info(str(index))
                _logger.info('inside created_ids')
                _logger.info(str(created_ids))

        _logger.info('final created_ids')
        _logger.info(str(created_ids))
        if created_ids:
            model_data = self.env.ref('philmer_books.philmer_book_form')
            action = { 'type': 'ir.actions.act_window',
                       'name': 'Created Books',
                       'res_model': 'philmer.book',
                       'domain': "[('id','in',[" + ','.join(map(str, created_ids)) + "])]",
                       'view_type':'form',
                       'view_mode': 'tree,form',
                       'views': [(False, 'tree'), (model_data.id, 'form')],
            }
            _logger.info(str(action))
            return action
        return True

    @api.multi
    def import_zip_file(self):
        for wizard in self:
            created_ids = []
            book_obj = self.env['philmer.book']
            author_obj = self.env['philmer.author']
            partner_obj = self.env['res.partner']
            participation_obj = self.env['philmer.book.participation']
            imported_id_obj = self.env['philmer.book.imported_id']
            lang_obj = self.env['res.lang']
            _logger.info('starting importing zip file of bibliophilia')
            #input_file_as_string = unicode(base64.decodestring(wizard.finput),'utf-16','ignore')
            zip_file = base64.decodestring(wizard.finput)
            dImages = {}
            csv_file = ''
            zip_fileIO = StringIO.StringIO(zip_file)
            if zipfile.is_zipfile(zip_fileIO):
                _logger.info('is zip file')
            else:
                _logger.info('not a zip file')
            # extract files from zip file into memory
            zip_fileIO = StringIO.StringIO(zip_file)
            full_zip = zipfile.ZipFile(zip_fileIO)
            for zip_file_info in full_zip.infolist():
                if zip_file_info.filename == 'BiblioPhilia_DB.csv':
                    csv_file = full_zip.read(zip_file_info.filename)
                    _logger.info('CSV File found')
                else:
                    if zip_file_info.filename[0:7] == 'covers/':
                        image_name = zip_file_info.filename[7:]
                        if image_name.index('.')>0:
                            image_name = image_name[0:image_name.index('.')]
                        dImages[image_name] = full_zip.read(zip_file_info.filename)
                        _logger.info('image file found %s -> %s' % (zip_file_info.filename,image_name))
                    else:
                        _logger.info('Unkwnown file type : %s' % zip_file_info.filename)
            input_file_as_string = unicode(csv_file,'utf-16','ignore')
            _logger.info(input_file_as_string)
            #covers_path = wizard.path
            #if covers_path[-1:] != '/':
            #    covers_path += '/'
            #_logger.info(covers_path)
            lines = input_file_as_string.split('\n')
            if len(lines) == 1:
                _logger.info('not windows end of line trying mac')
                lines = input_file_as_string.split('\r\n')
            if len(lines) == 1:
                _logger.info('not mac either, perhaps windows')
                lines = input_file_as_string.split('\r')
            # create language conversion table
            english_id = lang_obj.search([('iso_code','=','en_US')])[0].id
            french_id = lang_obj.search([('iso_code','=','fr_FR')])[0].id
            index = 0
            dHeaders = {}
            for line in lines:
                if index == 0:
                    headers = line.split(";")
                    index_header = 0
                    for header in headers:
                        dHeaders[header] = index_header
                        index_header += 1
                else:
                    fields = line.split(';')
                    new_fields = []
                    for field in fields:
                        new_field = field
                        if new_field[0:1] == u'"':
                            new_field = new_field[1:]
                        if new_field[-1:] == u'"':
                            new_field = new_field[:-1]
                        new_fields.append(new_field)
                    # verify if this record has not already been imported previously
                    already_ids = imported_id_obj.search([('source','=','Bibliophilia.Book'),('id_in_source','=',new_fields[dHeaders['id']])])
                    if not already_ids:
                        if len(new_fields) >= 30:
                            book_data = {}
                            # record the book data
                            book_data.update({'name':new_fields[dHeaders['title']]})
                            book_data.update({'sub_name':new_fields[dHeaders['subtitle']]})
                            book_data.update({'isbn':new_fields[dHeaders['isbn']]})
                            book_data.update({'pages':int(new_fields[dHeaders['pages']] or '0' )*1.0})
                            book_data.update({'description':new_fields[dHeaders['descr']]})
                            book_data.update({'book_type':'book'})
                            book_data.update({'book_format':'print'})
                            if new_fields[dHeaders['language']]:
                                if new_fields[dHeaders['language']] == u'Français':
                                    book_data.update({'language_id':french_id})
                                elif new_fields[dHeaders['language']] == u'Anglais':
                                    book_data.update({'language_id':english_id})
                            new_book = book_obj.create(book_data)
                            if new_book:
                                imported_id_obj.create({'source':'Bibliophilia.Book','id_in_source':new_fields[dHeaders['id']],'philmer_id':'philmer.book,'+str(new_book.id)})
                                created_ids.append(new_book.id)
                                _logger.info('after created_ids')
                                _logger.info(str(created_ids))
                                
                                # trying to get the cover
                                if dImages.has_key(str(new_fields[dHeaders['id']])):
                                    _logger.info('cover exists')
                                    new_book.cover = base64.encodestring(dImages[str(new_fields[dHeaders['id']])])
                                else:
                                    _logger.info('not existing cover')
                                # trying to get/create the author
                                bib_author_id = new_fields[dHeaders['author_id']]
                                bib_author_name = new_fields[dHeaders['author']]
                                if bib_author_id:
                                    imported_authors = imported_id_obj.search([('source','=','Bibliophilia.Author'),('id_in_source','=',bib_author_id)])
                                    if imported_authors:
                                        _logger.info('found author id')
                                        _logger.info(imported_authors[0].philmer_id.id)
                                        participation_obj.create({'author_id':imported_authors[0].philmer_id.id,'participation_type':'author','book_id':new_book.id})
                                    else:
                                        author = _search_or_create_author(author_obj,bib_author_name)
                                        if author:
                                            participation_obj.create({'author_id':author.id,
                                                                      'participation_type':'author',
                                                                      'book_id':new_book.id})
                                            imported_id_obj.create({'source':'Bibliophilia.Author',
                                                                    'id_in_source':bib_author_id,
                                                                    'philmer_id':'philmer.author,'+str(author.id)})
                                else:
                                    if bib_author_name:
                                        author = _search_or_create_author(author_obj,bib_author_name)
                                        if author:
                                            participation_obj.create({'author_id':author.id,'participation_type':'author','book_id':new_book.id})
                                # trying to get/create the editor
                                bib_editor_id = new_fields[dHeaders['editor_id']]
                                bib_editor_name = new_fields[dHeaders['publisher']]
                                if bib_editor_id:
                                    imported_editors = imported_id_obj.search([('source','=','Bibliophilia.Editor'),('id_in_source','=',bib_editor_id)])
                                    if imported_editors:
                                        _logger.info('found editor id')
                                        _logger.info(imported_editors[0].philmer_id.id)
                                        new_book.write({'editor_id':imported_editors[0].philmer_id.id})
                                    else:
                                        editor = _search_or_create_editor(partner_obj,bib_editor_name)
                                        if editor:
                                            new_book.write({'editor_id':editor.id})
                                            imported_id_obj.create({'source':'Bibliophilia.Editor',
                                                                    'id_in_source':bib_editor_id,
                                                                    'philmer_id':'res.partner,'+str(editor.id)})
                                else:
                                    if bib_editor_name:
                                        editor = _search_or_create_editor(partner_obj,bib_editor_name)
                                        if editor:
                                            new_book.write({'editor_id':editor.id})
                index += 1
                _logger.info('index')
                _logger.info(str(index))
                _logger.info('inside created_ids')
                _logger.info(str(created_ids))

        _logger.info('final created_ids')
        _logger.info(str(created_ids))
        if created_ids:
            model_data = self.env.ref('philmer_books.philmer_book_form')
            action = { 'type': 'ir.actions.act_window',
                       'name': 'Created Books',
                       'res_model': 'philmer.book',
                       'domain': "[('id','in',[" + ','.join(map(str, created_ids)) + "])]",
                       'view_type':'form',
                       'view_mode': 'tree,form',
                       'views': [(False, 'tree'), (model_data.id, 'form')],
            }
            _logger.info(str(action))
            return action
        return True
