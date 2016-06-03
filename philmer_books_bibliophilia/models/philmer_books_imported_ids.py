# -*- encoding: utf-8 -*-
import time
from openerp import tools
from openerp import models, fields, api, _
from openerp.exceptions import Warning

class philmer_book_imported_ids(models.Model):
    _name = 'philmer.book.imported_id'
    _description = 'ID in source file of item in Philmer''s Books'
    #_order = 'name'
    
    source = fields.Char('Source of external Data',required=True)
    #item_type = fields.Char('Type of item in Philmer''s Books',required=True)
    id_in_source = fields.Integer('ID in Source',required=True)
    #id_in_philmer = fields.Integer('ID in Philmer''s Books',required=True)
    philmer_id = fields.Reference(selection=[('philmer.book','Book'),('philmer.author','Author'),('res.partner','Editor')],string='Inserted as')
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
