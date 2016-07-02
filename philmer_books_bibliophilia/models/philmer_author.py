# -*- encoding: utf-8 -*-
import time
from openerp import tools
from openerp import models, fields, api, _
from openerp.exceptions import Warning

import logging

_logger = logging.getLogger(__name__)

class philmer_author(models.Model):
    _name = 'philmer.author'
    _inherit = 'philmer.author'

    @api.multi
    def unlink(self):
        imported_id_obj = self.env['philmer.book.imported_id']
        for author in self:
            _logger.info(str(author.id)+' - '+author.name)
            imported_id_obj.search([('philmer_id','=','philmer.author,'+str(author.id))]).unlink()
        return super(philmer_author, self).unlink()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
