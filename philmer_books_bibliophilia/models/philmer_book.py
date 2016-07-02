# -*- encoding: utf-8 -*-
import time
from openerp import tools
from openerp import models, fields, api, _
from openerp.exceptions import Warning

import logging

_logger = logging.getLogger(__name__)

class philmer_book(models.Model):
    _name = 'philmer.book'
    _inherit = 'philmer.book'

    @api.multi
    def unlink(self):
        imported_id_obj = self.env['philmer.book.imported_id']
        for book in self:
            _logger.info(str(book.id)+' - '+book.name)
            imported_id_obj.search([('philmer_id','=','philmer.book,'+str(book.id))]).unlink()
        return super(philmer_book, self).unlink()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
