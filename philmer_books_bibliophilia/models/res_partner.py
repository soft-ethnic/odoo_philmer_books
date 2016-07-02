# -*- encoding: utf-8 -*-
import time
from openerp import tools
from openerp import models, fields, api, _
from openerp.exceptions import Warning

import logging

_logger = logging.getLogger(__name__)

class res_partner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    @api.multi
    def unlink(self):
        imported_id_obj = self.env['philmer.book.imported_id']
        for partner in self:
            _logger.info(str(partner.id)+' - '+partner.name)
            imported_id_obj.search([('philmer_id','=','res.partner,'+str(partner.id))]).unlink()
        return super(res_partner, self).unlink()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
