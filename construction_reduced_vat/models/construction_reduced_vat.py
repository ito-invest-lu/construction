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
from odoo.exceptions import Warning, UserError, ValidationError

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
        
    def action_request(self):
        if self.filtered(lambda inv: inv.state != 'draft'):
            raise UserError(_("Agreement must be a draft in order to set it to requested."))
        return self.write({'state': 'requested'})
    
    def action_approve(self):
        if self.filtered(lambda inv: inv.state != 'draft' and inv.state != 'requested'):
            raise UserError(_("Agreement must be a draft or requested in order to set it to approved."))
        return self.write({'state': 'approved'})
        
    def action_reject(self):
        if self.filtered(lambda inv: inv.state != 'requested'):
            raise UserError(_("Agreement must be a requested in order to set it to rejected."))
        return self.write({'state': 'rejected'})
        
    def action_draft(self):
        return self.write({'state': 'draft','active':True})
        
    def action_archive(self):
        return self.write({'state': 'archived','active':False})
        
    active = fields.Boolean(default=True)
    
    agreement_code = fields.Char(string='Code',help='Agreement Code given by the administration', readonly=True, states={'draft': [('readonly', False)]})
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True, states={'draft': [('readonly', False)]}, required=True)
    
    name = fields.Char(compute='_compute_name', store=True)
    
    @api.depends('agreement_code','partner_id.name')
    def _compute_name(self):
        for rec in self :
            rec.name = "%s - %s" % (rec.agreement_code, rec.partner_id.name)
    
    agreement_total_amount = fields.Monetary(string="Total Amount", currency_field='company_currency_id', track_visibility='onchange', readonly=True, states={'draft': [('readonly', False)]})
    
    @api.constrains('agreement_total_amount')
    def _check_agreement_total_amount(self):
        for rec in self :
            if rec.agreement_total_amount > 357142.86 :
                raise ValidationError("The total amount shall not exeed 357.142,86€ (ie 50.000€ of VAT reduction).")
    
    invoice_ids = fields.One2many('account.move','reduced_vat_agreement_id',string="Invoices")
    agreement_remaining_amount = fields.Monetary(string="Remaining Amount", compute="_compute_remaining_amount", currency_field='company_currency_id', store=True)
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Company Currency", readonly=True)
    company_id = fields.Many2one('res.company', string='Company', change_default=True,
        required=True, readonly=True, states={'draft': [('readonly', False)]},
        default=lambda self: self.env['res.company']._company_default_get('account.move'))
    
    @api.depends('agreement_total_amount','invoice_ids.amount_untaxed','invoice_ids.state')
    def _compute_remaining_amount(self):
        _logger.info('_compute_remaining_amount')
        for rec in self:
            used_amount = 0
            tax_3  = self.env['ir.model.data'].xmlid_to_object('l10n_lu.%s_lu_2011_tax_VP-PA-3' % rec.company_id.id)
            tax_3_b  = self.env['ir.model.data'].xmlid_to_object('l10n_lu.%s_lu_2011_tax_VB-PA-3' % rec.company_id.id)
            for invoice in rec.invoice_ids:
                _logger.info('invoice %s' % invoice.name)
                if invoice.state in ('posted') :
                    for line in invoice.invoice_line_ids:
                        _logger.info('invoice line %s' % invoice.name)
                        if tax_3 in line.tax_ids or tax_3_b in line.tax_ids:
                            used_amount -= line.balance
            rec.agreement_remaining_amount = rec.agreement_total_amount - used_amount

class SaleOrder(models.Model):
    '''Sale Order'''
    _inherit = "sale.order"
    
    def _prepare_invoice(self):
        self.ensure_one()
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        agreement_ids = self.env['construction.reduced_vat_agreement'].search([('partner_id', '=', self.partner_id.id),('agreement_remaining_amount','>',0)])
        if len(agreement_ids) == 1 :
            invoice_vals['reduced_vat_agreement_id'] = agreement_ids[0].id
        return invoice_vals
        
    def _prepare_invoice_line(self, **optional_values):
        self.ensure_one()
        res = super(SaleOrder, self)._prepare_invoice_line(optional_values)
        tax_3  = self.env['ir.model.data'].xmlid_to_object('l10n_lu.%s_lu_2011_tax_VP-PA-3' % self.company_id.id)
        agreement_ids = self.env['construction.reduced_vat_agreement'].search([('partner_id', '=', self.partner_id.id),('agreement_remaining_amount','>',0)])
        if len(agreement_ids) == 1 :
            res['tax_ids'] = [(6, 0, [tax_3.id])]
        return res

class AccountInvoice(models.Model):
    '''Invoice'''
    _inherit = 'account.move'
    
    reduced_vat_agreement_id = fields.Many2one('construction.reduced_vat_agreement', string='Reduced VAT Agreement', readonly=True, states={'draft': [('readonly', False)]})
    
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        for invoice in self :
            tax_3  = self.env['ir.model.data'].xmlid_to_object('l10n_lu.%s_lu_2011_tax_VP-PA-3' % self.company_id.id)
            tax_3_b  = self.env['ir.model.data'].xmlid_to_object('l10n_lu.%s_lu_2011_tax_VB-PA-3' % self.company_id.id)
            tax_17 = self.env['ir.model.data'].xmlid_to_object('l10n_lu.%s_lu_2015_tax_VP-PA-17' % self.company_id.id)
            if invoice.reduced_vat_agreement_id :
                new_amount = 0
                has_line_at_3 = False
                for line in invoice.invoice_line_ids:
                    if not line.invoice_line_tax_ids:
                        raise UserError(_('All invoice lines shall have a VAT, use 0 if needed'))
                    if tax_3 in line.invoice_line_tax_ids or tax_3_b in line.invoice_line_tax_ids:
                        has_line_at_3 = True
                        break
                if invoice.reduced_vat_agreement_id.agreement_remaining_amount < 0 :
                    raise Warning(_('Reduced vat agreement maximum value exceeded !!'))
                if not has_line_at_3:
                    raise UserError(_('An agreement is defined however there is no line at 3%...'))
            else :
                for line in invoice.invoice_line_ids:
                    if not line.invoice_line_tax_ids:
                        raise UserError(_('All invoice lines shall have a VAT, use 0 if needed'))
        return res
        
    @api.onchange('reduced_vat_agreement_id')
    def onchange_reduced_vat_agreement_id(self):
        tax_17 = self.env['ir.model.data'].xmlid_to_object('l10n_lu.%s_lu_2015_tax_VP-PA-17' % self.company_id.id)
        tax_3  = self.env['ir.model.data'].xmlid_to_object('l10n_lu.%s_lu_2011_tax_VP-PA-3' % self.company_id.id)
        if self.reduced_vat_agreement_id :
            self.invoice_line_ids.write({
                    'tax_ids' : [(6, 0, [tax_3.id])],
                    'recompute_tax_line' : True
            })
        else :
            self.invoice_line_ids.write({
                    'tax_ids' : [(6, 0, [tax_17.id])],
                    'recompute_tax_line' : True
            })
        self._recompute_dynamic_lines(recompute_all_taxes=True)