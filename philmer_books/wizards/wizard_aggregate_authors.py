# -*- encoding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import Warning
import logging

_logger = logging.getLogger(__name__)

class wizard_aggregate_authors(models.TransientModel):
    _name = 'wizard_aggregate_authors'
    kept_author_id = fields.Many2one('philmer.author',string="Kept Author")
    aggregated_author_id = fields.Many2one('philmer.author',string="Author to aggregate",help="The books of this author will be transfered to the current author")
    
    @api.multi
    def aggregate_authors(self):
        for wizard in self:
            if wizard.kept_author_id and wizard.aggregated_author_id and wizard.kept_author_id.id != wizard.aggregated_author_id.id:
                participation_obj = self.env['philmer.book.participation']
                if wizard.aggregated_author_id.book_ids:
                    for book_participation in wizard.aggregated_author_id.book_ids:
                        book_participation.author_id = wizard.kept_author_id
                wizard.aggregated_author_id.unlink()
                _logger.info('Authors aggregated')
                _logger.info('The author %s [%i] is aggregated inside the record of the author %s [%i]' % (wizard.aggregated_author_id.name,
                                                                                                           wizard.aggregated_author_id.id,
                                                                                                           wizard.kept_author_id.name,
                                                                                                           wizard.kept_author_id.id))
        return True
