# -*- encoding: utf-8 -*-
import time
from openerp import tools
from openerp import models, fields, api, _
from openerp.exceptions import Warning

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
    editor = fields.Many2one('res.partner', string='Editor')
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
    serie_num = fields.Char('Number in the serie')
    description = fields.Text('Description/Back')
    language_id = fields.Many2one('res.lang',string='Language')
    active = fields.Boolean('Active',default=True)
    
class philmer_author(models.Model):
    _name = 'philmer.author'
    _description = 'Author of book, article, preface, illustration, ...'
    _order = 'name'
    
    name = fields.Char('Name')
    first_name = fields.Char('First Name')
    last_name = fields.Char('Last Name', required=True)
    description = fields.Text('Description')
    other_names = fields.Text('Other Names')
        
class philmer_book_participation(models.Model):
    _name = 'philmer.book.participation'
    _description = 'Link between Book and Author with the type of link'
    
    name = fields.Char('Name')
    author_name = fields.Char('Author and type')
    book_name = fields.Char('Book and type')
    author_id = fields.Many2one('philmer.author',required=True)
    book_id = fields.Many2one('philmer.book', required=True)
    participation_type = fields.Selection([('author','Author'),('illustrator','Inner illustrator'),('cover','Cover Illustrator'),('preface','Preface'),('scriptwriter','Scenarist')])
    
class philmer_reading(models.Model):
    _name = 'philmer.reading'
    _description = 'Mark the reading of a book by a user'

    name = fields.Char('Name')
    book_id = fields.Many2one('philmer.book', required=True)
    user_id = fields.Many2one('res.users', required=True)
    date = fields.Date('Date of end of reading', help='Leave it empty if current reading')
    cotation = fields.Integer(string='Cotation',min=0,max=20)
    note = fields.Text('Note',help='Note about this bbok by this user')
        
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
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
