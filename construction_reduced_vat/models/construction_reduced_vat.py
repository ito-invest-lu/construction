# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2015 be-cloud.be
#                       Jerome Sonnet <jerome.sonnet@be-cloud.be>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class ReducedVATAgreement(models.Model):
    '''Reduced VAT Agreement'''
    _name = 'construction.reduced_vat_agreement'
    _description = 'Reduced VAT Agreement'
    
    state = fields.Selection([
            ('draft', 'Draft'),
            ('requested', 'Requested'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('archived', 'Archived'),
        ], string='State', required=True, help="", default="draft")
        
    @api.multi
    def action_request(self):
        if self.filtered(lambda inv: inv.state != 'draft'):
            raise UserError(_("Agreement must be a draft in order to set it to requested."))
        return self.write({'state': 'requested'})
    
    @api.multi
    def action_approve(self):
        if self.filtered(lambda inv: inv.state != 'draft' and inv.state != 'requested'):
            raise UserError(_("Agreement must be a draft or requested in order to set it to approved."))
        return self.write({'state': 'approved'})
        
    @api.multi
    def action_reject(self):
        if self.filtered(lambda inv: inv.state != 'requested'):
            raise UserError(_("Agreement must be a requested in order to set it to rejected."))
        return self.write({'state': 'rejected'})
        
    @api.multi
    def action_draft(self):
        return self.write({'state': 'draft','active':True})
        
    @api.multi
    def action_archive(self):
        return self.write({'state': 'archived','active':False})
        
    active = fields.Boolean(default=True)
    
    agreement_code = fields.Char(string='Code',help='Agreement Code given by the administration', readonly=True, states={'draft': [('readonly', False)]})
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True, states={'draft': [('readonly', False)]}, required=True)
    
    name = fields.Char(compute='_compute_name', store=True)
    
    @api.one
    @api.depends('agreement_code','partner_id.name')
    def _compute_name(self):
       self.name = "%s - %s" % (self.agreement_code, self.partner_id.name)
    
    agreement_total_amount = fields.Monetary(string="Total Amount", currency_field='company_currency_id', track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    
    @api.one
    @api.constrains('agreement_total_amount')
    def _check_agreement_total_amount(self):
        if self.agreement_total_amount > 357142.86 :
            raise ValidationError("The total amount shall not exeed 357.142,86€ (ie 50.000€ of VAT reduction).")
    
    invoice_ids = fields.One2many('account.invoice','reduced_vat_agreement_id',string="Invoices")
    agreement_remaining_amount = fields.Monetary(string="Remaining Amount", compute="_compute_remaining_amount", currency_field='company_currency_id', store=True)
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency", readonly=True)
    company_id = fields.Many2one('res.company', string='Company', change_default=True,
        required=True, readonly=True, states={'draft': [('readonly', False)]},
        default=lambda self: self.env['res.company']._company_default_get('account.invoice'))
    
    @api.one
    @api.depends('agreement_total_amount','invoice_ids.amount_untaxed')
    def _compute_remaining_amount(self):
        used_amount = 0
        tax_3  = self.env['ir.model.data'].xmlid_to_object('l10n_lu.1_lu_2011_tax_VP-PA-3')
        tax_3_b  = self.env['ir.model.data'].xmlid_to_object('l10n_lu.1_lu_2011_tax_VB-PA-3')
        for invoice in self.invoice_ids:
            for line in invoice.invoice_line_ids:
                if tax_3 in line.invoice_line_tax_ids or tax_3_b in line.invoice_line_tax_ids:
                    used_amount += line.price_subtotal_signed
        self.agreement_remaining_amount = self.agreement_total_amount - used_amount

class SaleOrder(models.Model):
    '''Sale Order'''
    _inherit = "sale.order"
    
    @api.multi
    def _prepare_invoice(self):
        self.ensure_one()
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        agreement_ids = self.env['construction.reduced_vat_agreement'].search([('partner_id', '=', self.partner_id.id),('agreement_remaining_amount','>',0)])
        if len(agreement_ids) == 1 :
            invoice_vals['reduced_vat_agreement_id'] = agreement_ids[0].id
        return invoice_vals
        
    
class AccountInvoice(models.Model):
    '''Invoice'''
    _inherit = 'account.invoice'
    
    reduced_vat_agreement_id = fields.Many2one('construction.reduced_vat_agreement', string='Reduced VAT Agreement', readonly=True, states={'draft': [('readonly', False)]})
    
    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        for invoice in self :
            tax_3  = self.env['ir.model.data'].xmlid_to_object('l10n_lu.1_lu_2011_tax_VP-PA-3')
            tax_3_b  = self.env['ir.model.data'].xmlid_to_object('l10n_lu.1_lu_2011_tax_VB-PA-3')
            if self.reduced_vat_agreement_id :
                new_amount = 0
                for line in invoice.invoice_line_ids:
                    if tax_3 in line.invoice_line_tax_ids or tax_3_b in line.invoice_line_tax_ids:
                        new_amount += line.price_subtotal_signed
                if self.reduced_vat_agreement_id.agreement_remaining_amount < new_amount - 0.01 :
                    raise UserError(_("The reduced tva agreement total amount is exceeded."))
            return res
        
    @api.onchange('reduced_vat_agreement_id')
    def onchange_reduced_vat_agreement_id(self):
        tax_17 = self.env['ir.model.data'].xmlid_to_object('l10n_lu.1_lu_2015_tax_VP-PA-17')
        tax_3  = self.env['ir.model.data'].xmlid_to_object('l10n_lu.1_lu_2011_tax_VP-PA-3')
        if self.reduced_vat_agreement_id :
            self.invoice_line_ids.write({
                    'invoice_line_tax_ids' : [(6, 0, [tax_3.id])]
            })
        else :
            self.invoice_line_ids.write({
                    'invoice_line_tax_ids' : [(6, 0, [tax_17.id])]
            })