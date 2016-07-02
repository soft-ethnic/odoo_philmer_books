# -*- encoding: utf-8 -*-
import time
from openerp import tools
from openerp import models, fields, api, _
from openerp.exceptions import Warning
import logging

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

class philmer_book(models.Model):
    _name = 'philmer.book'
    _description = 'Book and/or Issues of Magazines'
    _order = 'name'
    
    name = fields.Char('Name', required=True)
    sub_name = fields.Char('Sub Name', help='Optional Sub Name')
    original_name = fields.Char('Original Name in the original language')
    book_type = fields.Selection([('book','Book'),('comic','BD, Comic, Manga'),('zine_name','Magazine'),('zine_issue','Magazine Issue'),('article','Article'),('anthology','Anthology'),('novel','Novel')],'Type')
    book_format = fields.Selection([('ebook','eBook'),('print','Printed'),('printed_ebook','eBook and Printed')],'Format')
    parution_date = fields.Date('Parution')
    author_ids = fields.One2many('philmer.book.participation', 'book_id', string='Authors')
    reading_ids = fields.One2many('philmer.book.reading', 'book_id', string='Readings')
    editor_id = fields.Many2one('res.partner', string='Editor')
    collection = fields.Char('Collection')
    pages = fields.Float('Pages', (6,2))
    first_page = fields.Integer('First Page')
    tag_ids = fields.Many2many('philmer.book.tag', relation='philmer_books_tags', column1='book_id', column2='tag_id', string='Tags')
    borrow_date = fields.Date('Borrow Date')
    borrower_id = fields.Many2one('res.partner', string='Borrower')
    classification = fields.Char('Classification')
    parent_id = fields.Many2one('philmer.book')
    category_id = fields.Many2one('philmer.book.category', string='Category')
    serie_id = fields.Many2one('philmer.book.serie', string='Serie/Cycle')
    number = fields.Char('Number',help='Number in the serie, or magazine number')
    description = fields.Text('Description/Back')
    language_id = fields.Many2one('res.lang',string='Language')
    isbn = fields.Char('ISBN')
    cover = fields.Binary('Cover')
    active = fields.Boolean('Active',default=True)
    
    @api.constrains('isbn')
    def _valid_isbn(self):
        # ISBN : 13 digits
        #        first three numbers must be '978', or '979' (as today)
        #        9 chiffres suivants sont la vraie clé
        #        le dernier chiffre est une clé de validation des 12 premiers
        for book in self:
            if book.isbn:
                if len(book.isbn) != 13:
                    raise models.ValidationError('Only ISBN 13 digits are allowed : %s is not correct.' % book.isbn)
                else:
                    if not book.isbn.isdigit():
                        raise models.ValidationError('Only digits are allowed in ISBN 13 digits : %s is not correct.' % book.isbn)
                    else:
                        if book.isbn[0:3] not in ('978','979'):
                            raise models.ValidationError('The ISBN numbers MUST begin with 978 or 979 : %s is not correct.' % book.isbn)
                        else:
                            value = 0
                            odd = True
                            for carac in book.isbn[0:12]:
                                if odd:
                                    odd = False
                                    value += int(carac)
                                else:
                                    odd = True
                                    value += (3*int(carac))
                            if int(book.isbn[12]) != ((10-(value % 10)) % 10):
                                raise models.ValidationError('The check digit of %s is not correct : %s is different from the good value of %s [%s].' % (book.isbn,book.isbn[12],str(((10-(value % 10)) % 10)),str(value)))

class philmer_author(models.Model):
    _name = 'philmer.author'
    _description = 'Author of book, article, preface, illustration, ...'
    _order = 'name'

    @api.depends('first_name','last_name')
    def _get_full_name(self):
        for author in self:
            res = author.last_name
            if author.first_name:
                res += ', ' + author.first_name
            author.name = res
    def _search_full_name(self,operator,value):
        return ['|',('last_name','ilike',value),('first_name','ilike',value)]
    
    name = fields.Char('Name',compute='_get_full_name',
                              search='_search_full_name',
                              store=True,compute_sudo=False)
    first_name = fields.Char('First Name')
    last_name = fields.Char('Last Name', required=True)
    book_ids = fields.One2many('philmer.book.participation', 'author_id', string='Books')
    description = fields.Text('Description')
    other_names = fields.Text('Other Names')
    active = fields.Boolean('Active', default=True)
        
    @api.multi
    def split_names(self):
        for author in self:
            if author.last_name and ',' in author.last_name:
                _logger.info(author.last_name+' ['+str(author.id)+']')
                _logger.info('to split')
                old_author_id = author.id
                new_names = author.last_name.split(',')
                author_obj = self.env['philmer.author']
                participation_obj = self.env['philmer.book.participation']
                new_author_ids = []
                for new_name in new_names:
                    _logger.info(new_name)
                    new_author = _search_or_create_author(author_obj,new_name)
                    if new_author:
                        new_author_ids.append(new_author.id)
                _logger.info(str(new_author_ids))
                if new_author_ids:
                    for book_participation in author.book_ids:
                        _logger.info(str(book_participation))
                        book_participation.author_id = new_author_ids[0]
                        for new_author_id in new_author_ids[1:]:
                            participation_obj.create({'author_id':new_author_id,
                                                      'book_id':book_participation.book_id.id,
                                                      'participation_type':book_participation.participation_type})
                    author.unlink()
                        

class philmer_book_participation(models.Model):
    _name = 'philmer.book.participation'
    _description = 'Link between Book and Author with the type of link'
    
    name = fields.Char('Name',compute='_get_name',
                              search='_search_name',
                              store=True,compute_sudo=False)
    author_name = fields.Char('Author and type',compute='_get_author_name',
                                                search='_search_author_name',
                                                store=True,compute_sudo=False)
    book_name = fields.Char('Book and type',compute='_get_book_name',
                                            search='_search_book_name',
                                            store=True,compute_sudo=False)
    author_id = fields.Many2one('philmer.author',required=True ,ondelete='cascade')
    book_id = fields.Many2one('philmer.book', required=True,ondelete='cascade')
    participation_type = fields.Selection([('author','Author'),('illustrator','Inner illustrator'),('cover','Cover Illustrator'),('preface','Preface'),('scriptwriter','Scenarist')])

    @api.depends('author_id','participation_type')
    def _get_author_name(self):
        for part in self:
            res = part.author_id.name
            if part.participation_type:
                res += ' [' + part.participation_type + ']'
            part.author_name = res
    def _search_author_name(self,operator,value):
        return []

    @api.depends('book_id','participation_type')
    def _get_book_name(self):
        for part in self:
            res = part.book_id.name
            if part.participation_type:
                res = part.participation_type + ' of ' + res
            part.book_name = res
    def _search_book_name(self,operator,value):
        return []

    @api.depends('book_id','author_id','participation_type')
    def _get_name(self):
        for part in self:
            res = part.author_id.name
            if part.participation_type:
                res += ' [' + part.participation_type + ']'
            res += ' of ' + part.book_id.name
            part.name = res
    def _search_name(self,operator,value):
        return []

class philmer_reading(models.Model):
    _name = 'philmer.reading'
    _description = 'Mark the reading of a book by a user'

    name = fields.Char('Name',compute='_get_name',
                              store=True,compute_sudo=False)
    book_id = fields.Many2one('philmer.book', required=True)
    user_id = fields.Many2one('res.users', required=True)
    date = fields.Date('Date of end of reading', help='Leave it empty if current reading')
    cotation = fields.Integer(string='Cotation',min=0,max=20)
    note = fields.Text('Note',help='Note about this bbok by this user')

    @api.depends('book_id','user_id','date')
    def _get_name(self):
        for reading in self:
            if reading.date:
                res = date + ' '
            else:
                res = '0000-00-00 '
            res += user_id.name + ' ' + book_id.name
            reading.name = res
        
class philmer_book_category(models.Model):
    _name = 'philmer.book.category'
    _description = 'Category of books, in an hierarchical way, to permit "Litterature / Science Fiction / Hard Science" as category'
    _parent_store = True # to enable the auto-mananagement of parent_left and right
    _order = 'name'
    
    name = fields.Char('Category')
    parent_id = fields.Many2one('philmer.book.category', string='Parent Category', ondelete='restrict', index=True)
    child_ids = fields.One2many('philmer.book.category', 'parent_id',string='Sub categories')
    parent_left = fields.Integer(index=True)
    parent_right = fields.Integer(index=True)
    book_ids = fields.One2many('philmer.book', 'category_id', string='Books')
    active = fields.Boolean('Active', default=True)
    
    @api.constrains('parent_id')
    def _check_hierarchy(self):
        if not self._check_recursion():
            raise models.ValidationError('Error! You cannont create cyclic categories !')
            
class philmer_book_tag(models.Model):
    _name = 'philmer.book.tag'
    _description = 'Books Tags'
    _order = 'name'
    
    name = fields.Char('Name', required=True)
    book_ids = fields.Many2many('philmer.book', relation='philmer_books_tags', column1='tag_id', column2='book_id', string='Books')
    active = fields.Boolean('Active', default=True)

class philmer_book_serie(models.Model):
    _name = 'philmer.book.serie'
    _description = 'Serie of books; Cycle of books'
    _order = 'name'
    
    name = fields.Char('Serie Name')
    book_ids = fields.One2many('philmer.book', 'serie_id', string='Books')
    active = fields.Boolean('Active', default=True)
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
