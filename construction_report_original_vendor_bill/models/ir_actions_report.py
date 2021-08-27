# -*- coding: utf-8 -*-

import os
import tempfile

import logging

from odoo import models, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _post_pdf(self, save_in_attachment, pdf_content=None, res_ids=None):
        '''Merge the existing attachments in a zip file and add doc number and
        journal on the first page.
        :param save_in_attachment: The retrieved attachments as map record.id -> attachment_id.
        :param pdf_content: The pdf content newly generated by wkhtmltopdf.
        :param res_ids: the ids of record to allow postprocessing.
        :return: The pdf content of the merged pdf.
        '''
        # don't include the generated dummy report
        if self.report_name == 'account.report_original_vendor_bill' :
            _logger.info(res_ids)
            _logger.info(save_in_attachment)
            record_map = {r.id: r for r in self.env[self.model].browse([res_id for res_id in save_in_attachment.keys() if res_id])}
            _logger.info(record_map)
            with tempfile.TemporaryDirectory() as dump_dir:
                for (id, stream) in save_in_attachment.items():
                    record = record_map[id]
                    with open(os.path.join(dump_dir, "%s-%s (%s : %s EUR).pdf" % (record.jounal_id.code,record.name, record.partner_id.name, record.amount_total)), 'w') as f:
                        f.write(stream.content)
                        
                with zipfile.ZipFile(os.path.join(dump_dir, 'original_vendor_bill.zip'), 'w') as zfile:
                    for root, dirs, files in os.walk(dump_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            zfile.write(file_path, file_path.split(container).pop())
                
                
            
        #     pdf_content = None
        #     res_ids = None
        #     if not save_in_attachment:
        #         raise UserError(_("No original vendor bills could be found for any of the selected vendor bills."))
        # return super(IrActionsReport, self)._post_pdf(save_in_attachment, pdf_content=pdf_content, res_ids=res_ids)

    # def _postprocess_pdf_report(self, record, buffer):
    #     # don't save the 'account.report_original_vendor_bill' report as it's just a mean to print existing attachments
    #     if self.report_name == 'account.report_original_vendor_bill':
    #         return None
    #     res = super(IrActionsReport, self)._postprocess_pdf_report(record, buffer)
    #     if self.model == 'account.move' and record.state == 'posted' and record.is_sale_document(include_receipts=True):
    #         attachment = self.retrieve_attachment(record)
    #         if attachment:
    #             attachment.register_as_main_attachment(force=False)
    #     return res
