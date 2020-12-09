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

from openerp import api, fields, models, _
from openerp.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class BuildingAsset(models.Model):
    '''Building Asset'''
    _name = 'construction.building_asset'
    _description = 'Building Asset'

    _order = 'name'

    title = fields.Char(string="Title")

    name = fields.Char(string="Name", compute='_compute_name', store=True)

    active = fields.Boolean(string="Active", default=True)

    @api.depends('title','partner_id.name')
    def _compute_name(self):
        for rec in self :
            if rec.partner_id and rec.title:
                rec.name = "%s - %s" % (rec.title, rec.partner_id.name)
            elif rec.partner_id:
                rec.name = rec.partner_id.name
            else:
                rec.name = rec.title

    state = fields.Selection([
            ('development', 'In development'),
            ('onsale', 'On sale'),
            ('proposal', 'Proposal'),
            ('sold', 'Sold'),
        ], string='State', required=True, help="",default="development")

    type = fields.Selection([
            ('appartment', 'Appartment'),
            ('duplex', 'Duplex'),
            ('house', 'House'),
            ('contiguous', 'Contiguous House'),
            ('parking', 'Parking'),
        ], string='Type of asset', required=True, help="")

    address_id = fields.Many2one('res.partner', string='Asset address', domain="[('type', '=', 'delivery')]")

    partner_id = fields.Many2one('res.partner', string='Customer', ondelete='restrict', help="Customer for this asset.")

    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)

    confirmed_lead_id = fields.Many2one('crm.lead', string='Confirmed Lead')

    candidate_lead_ids = fields.One2many('crm.lead', 'building_asset_id', string='Candidate Leads', domain=['|',('active','=',True),('active','=',False)])
    
    analytic_account = fields.Char(string="BookIn Analytic")

    @api.onchange('confirmed_lead_id')
    def update_confirmed_lead_id(self):
        self.partner_id = self.confirmed_lead_id.partner_id
        self.state = 'sold'

    sale_order_ids = fields.One2many('sale.order', 'building_asset_id', string="Sale Orders", readonly=True)

    all_tags = fields.Many2many('sale.order.tag', string='SO', compute="_compute_tags")
    missing_tags = fields.Many2many('sale.order.tag', string='Missing SO', compute="_compute_tags")

    def _compute_tags(self):
        for rec in self :
            rec.all_tags = rec.sale_order_ids.filtered(lambda o: o.state == 'sale').mapped('construction_tag_ids')
            rec.missing_tags = rec.env['sale.order.tag'].search([]) - rec.all_tags

    invoice_ids = fields.One2many('account.move','building_asset_id', string="Invoices", readonly=True)

class SaleOrder(models.Model):
    '''Sale Order'''
    _inherit = "sale.order"

    building_asset_id = fields.Many2one('construction.building_asset', string='Building Asset', ondelete='restrict')

    is_main_order = fields.Boolean('Main Order for this building asset')

    so_summary = fields.Text("SO Summary", compute="_compute_so_summary")

    active = fields.Boolean(default=True, help="If you uncheck the active field, it will disable the sale order without deleting it.")

    def _compute_so_summary(self):
        for rec in self:
            if not rec.is_main_order:
                rec.so_summary = ', '.join(rec.order_line.mapped('name'))
            else :
                rec.so_summary = 'voir détails...'

    # @api.constrains('is_main_order')
    # def _check_parent_id(self):
    #     main_order_count = self.env['sale.order'].search_count([('building_asset_id','=',self.building_asset_id.id),('is_main_order','=','true')])
    #     if main_order_count > 1 :
    #         raise ValidationError(_('Error ! You cannot have mutiple main order for an asset.'))

    @api.onchange('state')
    def update_asset_state(self):
        if self.state == 'sent':
            self.building_asset_id.state = 'proposal'
            # TODO add to the candidate lead_ids
        if self.state == 'sale' and self.is_main_order:
            self.building_asset_id.state = 'sold'
            self.confirmed_lead_id.id = self.opportunity_id.id
        if self.state == 'sale' and not self.is_main_order:
             for line in self.order_line:
                 line.qty_delivered = line.product_uom_qty

    @api.onchange('building_asset_id')
    def update_building_asset_id(self):
        if self.building_asset_id:
            self.company_id = self.building_asset_id.company_id

    @api.onchange('partner_id')
    def onchange_parter(self):
        if self.partner_id:
            if not self.building_asset_id :
                asset_id = self.env['construction.building_asset'].search([('partner_id','=',self.partner_id.id)])
                if asset_id :
                    self.building_asset_id = asset_id[0]

    def _prepare_invoice(self):
        old_company_id = self.env.user.company_id
        self.env.user.company_id = self.company_id
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals['building_asset_id'] = self.building_asset_id.id or False
        self.env.user.company_id = old_company_id
        return invoice_vals

    amount_outstanding = fields.Monetary(string='Outstanding Amount', store=True, readonly=True, compute='_amount_outstanding')

    @api.depends('order_line.price_subtotal','order_line.qty_invoiced','order_line.product_uom_qty')
    def _amount_outstanding(self):
        """
        Compute the outstanding amounts of the SO.
        """
        for order in self:
            amount_outstanding = 0.0
            for line in order.order_line :
                amount_outstanding += line.price_subtotal * (line.product_uom_qty-line.qty_invoiced)
            order.update({
                'amount_outstanding': order.pricelist_id.currency_id.round(amount_outstanding),
            })

    construction_tag_ids = fields.Many2many('sale.order.tag', 'construction_sale_order_tag_rel', 'order_id', 'tag_id', string='Tags', copy=False)

class SaleOrderTag(models.Model):
    _name = 'sale.order.tag'
    _description = 'Sale Order Tags'
    name = fields.Char(string='Analytic Tag', index=True, required=True)
    color = fields.Integer('Color Index')
    active = fields.Boolean(default=True, help="Set active to false to hide the Sale Order Tag without removing it.")

    analytic_account = fields.Char(string="BookIn Analytic")

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    building_asset_id = fields.Many2one('construction.building_asset', string='Building Asset', related="order_id.building_asset_id", store=True)

    # is_next_candidate = fields.Boolean(compute='_compute_is_next_candidate',search='_search_next_candidate')

    # @api.depends('order_id.order_line.qty_delivered','order_id.order_line.product_uom_qty')
    # def _compute_is_next_candidate(self):
    #     for line in self:
    #         if line.qty_delivered == line.product_uom_qty :
    #             line.is_next_candidate = False
    #         else :
    #             previous_line = self.env['sale.order.line'].search([
    #                 ('order_id', '=', line.order_id.id),
    #                 ('sequence', '<', line.sequence)
    #                 ], limit=1, order='sequence desc')
    #             if previous_line:
    #                 if previous_line.qty_delivered == line.product_uom_qty :
    #                     line.is_next_candidate = True
    #                 else :
    #                     line.is_next_candidate = False

    # def _search_next_candidate(self, operator, value):
    #     res = []
    #     assert operator in ('=', '!=', '<>') and value in (True, False), 'Operation not supported'
    #     if (operator == '=' and value is True) or (operator in ('<>', '!=') and value is False):
    #         search_operator = 'in'
    #     else:
    #         search_operator = 'not in'
    #     self.env.cr.execute("""SELECT id FROM
    #                             (SELECT
    #                                 (select id from sale_order_line where order_id = so.id AND qty_delivered = 0 AND qty_invoiced = 0 ORDER BY sequence ASC LIMIT 1) AS id
    #                                 FROM sale_order so WHERE so.state = 'sale'
    #                             )
    #                             out WHERE out.id IS NOT NULL;""")
    #     res_ids = [x[0] for x in self.env.cr.fetchall()]
    #     res.append(('id', search_operator, res_ids))
    #     return res


    def action_deliver_line(self):
        for order_line in self:
            order_line.write({'qty_delivered' : order_line.product_uom_qty})

class CrmLean(models.Model):
    '''CRM Lead'''
    _inherit = "crm.lead"

    building_asset_id = fields.Many2one('construction.building_asset', string='Building Asset', ondelete='restrict')

    def _convert_opportunity_data(self, customer, team_id=False):
        res = super(CrmLean, self)._convert_opportunity_data(self, customer, team_id)
        res['building_asset_id'] = self.building_asset_id.id or False

class Invoice(models.Model):
    '''Invoice'''
    _inherit = 'account.move'

    building_asset_id = fields.Many2one('construction.building_asset', string='Building Asset', ondelete='restrict')

    first_line_tax_id = fields.Many2one('account.tax', string='Fist Line Tax', compute='_compute_first_line_tax_id')

    summary = fields.Text("Summary", compute="_compute_summary")

    def _compute_summary(self):
        for rec in self:
            rec.summary = ', '.join(rec.invoice_line_ids.mapped('name'))

    def _compute_first_line_tax_id(self):
        for invoice in self:
            tax_id = False
            if len(invoice.invoice_line_ids) > 0 :
                line = invoice.invoice_line_ids[0]
                if len(line.invoice_line_tax_ids) > 0 :
                    tax_id = line.invoice_line_tax_ids[0]
            invoice.first_line_tax_id = tax_id
            
    state = fields.Selection(selection_add([('to_approve','To approve'),('approved','Approved'),('posted')])
    
    def to_approve(self):
        return self.write({'state': 'to_approve'})

    def approved(self):
        return self.write({'state': 'approved'})

class Partner(models.Model):
    '''Partner'''
    _inherit = 'res.partner'

    matricule = fields.Char(string="Matricule")

    building_asset_ids = fields.One2many('construction.building_asset', 'partner_id', string='Building Assets')
    building_asset_count = fields.Integer(compute='_compute_building_asset_count', string='# of Assets')

    def _compute_building_asset_count(self):
        asset_data = self.env['construction.building_asset'].read_group(domain=[('partner_id', 'child_of', self.ids)],
                                                      fields=['partner_id'], groupby=['partner_id'])
        # read to keep the child/parent relation while aggregating the read_group result in the loop
        partner_child_ids = self.read(['child_ids'])
        mapped_data = dict([(m['partner_id'][0], m['partner_id_count']) for m in asset_data])
        for partner in self:
            # let's obtain the partner id and all its child ids from the read up there
            item = next(p for p in partner_child_ids if p['id'] == partner.id)
            partner_ids = [partner.id] + item.get('child_ids')
            # then we can sum for all the partner's child
            partner.building_asset_count = sum(mapped_data.get(child, 0) for child in partner_ids)

class PurchaseOrder(models.Model):
    '''Purchase Order'''
    _inherit = "purchase.order"

    building_asset_id = fields.Many2one('construction.building_asset', string='Building Asset', ondelete='restrict')
    
    construction_tag_ids = fields.Many2many('sale.order.tag', 'construction_purchase_order_tag_rel', 'order_id', 'tag_id', string='Tags', copy=False)
    
    po_summary = fields.Text("PO Summary", compute="_compute_po_summary")
    
    def _compute_po_summary(self):
        for rec in self:
            rec.po_summary = ', '.join(rec.order_line.mapped('name'))