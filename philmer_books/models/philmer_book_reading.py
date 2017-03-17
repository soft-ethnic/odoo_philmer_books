# -*- encoding: utf-8 -*-
import time
from openerp import tools
from openerp import models, fields, api, _
from openerp.exceptions import Warning

class philmer_book_reading(models.Model):
    _name = 'philmer.book.reading'
    _description = 'Record the reading of a book by a user'
    _order = 'reading_date desc'
    
    name = fields.Char('Name',compute='_get_name',
                              store=True,compute_sudo=False)
    user_name = fields.Char('User and date',compute='_get_user_name',
                                            store=True,compute_sudo=False)
    book_name = fields.Char('Book and date',compute='_get_book_name',
                                            store=True,compute_sudo=False)
    user_id = fields.Many2one('res.users',required=True ,ondelete='cascade')
    book_id = fields.Many2one('philmer.book', required=True,ondelete='cascade')
    reading_date = fields.Char('Date',help="Format : YYYY-MM-DD; Date can be partial : YYYY or YYYY-MM")
    cotation = fields.Integer('Cotation',help='Between 0 and 10')
    
    @api.depends('user_id','reading_date')
    def _get_user_name(self):
        for reading in self:
            res = reading.user_id.name
            if reading.reading_date:
                res += _(' on ') + reading.reading_date
            reading.user_name = res

    @api.depends('book_id','reading_date')
    def _get_book_name(self):
        for reading in self:
            res = reading.book_id.name
            if reading.reading_date:
                res += _(' on ') + reading.reading_date
            reading.book_name = res

    @api.depends('book_id','user_id','reading_date')
    def _get_name(self):
        for reading in self:
            res = _('%s has read %s') % (reading.user_id.name,reading.book_id.name)
            if reading.reading_date:
                res += _(' on ') + reading.reading_date
            reading.name = res

