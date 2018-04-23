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
from openerp.exceptions import UserError

_logger = logging.getLogger(__name__)

DEFAULT_TASKS = [
    'Démolition',
    'Terrassement',
    'Gros Oeuvre',
    'Charpente',
    'Couverture',
    'Chassis',
    'Encastrement Hvac',
    'Plafonnage',
    'Chape',
    'Carrelage',
    'Peinture',
    'Aménagements extérieur',
    'SAV'
]

DEFAULT_STAGES = [
    'project_stage_not_started',
    'project_stage_ongoing',
    'project_stage_finished',
]

class BuildingSite(models.Model):
    '''Building Site'''
    _name = 'construction.building_site'
    _description = 'Building Site'
    
    _inherits = {'project.project': "project_id"}
    
    _order = 'name'
    
    construction_state = fields.Selection([
            ('development', 'In development'),
            ('onsale', 'On Sale'),
            ('construction', 'In Construction'),
            ('waranty', 'Waranty'),
            ('long_waranty', 'Long Wanranty'),
            ('archived', 'Archived'),
        ], string='State', required=True, help="")
    
    @api.onchange('construction_state')
    def update_project_state(self):
        if self.construction_state == 'construction':
            self.state = 'open'
        if self.construction_state == 'waranty':
            self.state = 'close'
    
    project_id = fields.Many2one('project.project', 'Project',
            help="Link this site to a project",
            ondelete="cascade", required=True, auto_join=True)
    
    @api.onchange('project_id')
    def update_project(self):
        self.building_site_id = self.id
        
    type = fields.Selection([
            ('single', 'Single'),
            ('double', 'Double'),
            ('residency', 'Residency'),
        ], string='Type of building', required=True, help="")
    
    address_id = fields.Many2one('res.partner', string='Site adress', domain="[('type', '=', 'delivery')]")
    notes = fields.Text(string='Notes')
    
    acquisition_lead = fields.Many2one('crm.lead', string='Acquisition Lead')
    asset_ids = fields.One2many('construction.building_asset', 'site_id', string="Building Assets")
    asset_count = fields.Integer(compute='_compute_asset_count')
    
    def _compute_asset_count(self):
        for site in self:
            site.asset_counts = len(site.asset_ids)
    
class Project(models.Model):
    _inherit = "project.project"
    
    building_site_id = fields.Many2one('construction.building_site', string='Building Site', ondelete='cascade')

    @api.one
    def add_default_tasks(self):
        for stage in DEFAULT_STAGES:
            res_model, res_id = self.env['ir.model.data'].get_object_reference('construction',stage)
            stage_id = self.env[res_model].browse(res_id)
            stage_id.write({
                'project_ids' : [(4, self.id, False)]
            })
        res_model, res_id = self.env['ir.model.data'].get_object_reference('construction','project_stage_not_started')
        stage_id = self.env[res_model].browse(res_id)
        i = 0
        for task_name in DEFAULT_TASKS:
            self.env['project.task'].create({
                'sequence' : i * 10 + 5,
                'name' : task_name, 
                'project_id' : self.id,
                'stage_id' : stage_id.id,
            })
            i = i + 1

    @api.one
    def upgrade_as_building_site(self):
        if self.building_site_id:
            raise UserError('This project is already associated to a building site')
        site = self.env['construction.building_site'].create({
            'name' : self.name,
            'construction_state' : 'construction',
            'type' : 'single',
        })
        project_id = site.project_id
        site.write({
            'project_id' : self.id
        })
        project_id.unlink()
        asset = self.env['construction.building_asset'].create({
            'name' : self.name,
            'site_id' : site.id,
            'partner_id' : self.partner_id.id or False,
            'state' : 'sold',
            'type' : 'house',
        })
        
    @api.model
    def default_get(self, fields):
        result = super(Project, self).default_get(fields)
        default_type_ids = [self.env.ref('construction.project_stage_not_started').id,self.env.ref('construction.project_stage_ongoing').id,self.env.ref('construction.project_stage_finished').id]
        result.update({'type_ids': list(set(default_type_ids))})
        
    @api.one
    def fix_task_type(self):
        default_type_ids = [self.env.ref('construction.project_stage_not_started').id,self.env.ref('construction.project_stage_ongoing').id,self.env.ref('construction.project_stage_finished').id]
        self.type_ids = [(6,0,default_type_ids)]
    
class BuildingAsset(models.Model):
    '''Building Asset'''
    _name = 'construction.building_asset'
    _description = 'Building Asset'
    
    _order = 'name'
    
    title = fields.Char(string="Title")
    
    name = fields.Char(string="Name", compute='_compute_name', store=True)
    
    @api.one
    @api.depends('title','partner_id.name')
    def _compute_name(self):
        if self.partner_id and self.title:
            self.name = "%s - %s" % (self.title, self.partner_id.name)
        elif self.partner_id:
            self.name = self.partner_id.name
        else:
            self.name = self.title
    
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
    
    site_id = fields.Many2one('construction.building_site', string='Building Site', ondelete='cascade')
   
    address_id = fields.Many2one('res.partner', string='Asset address', compute='_compute_address_id')
    
    asset_address_id = fields.Many2one('res.partner', string='Asset address', domain="[('type', '=', 'delivery')]")
    
    @api.depends('site_id','site_id.address_id','asset_address_id')
    def _compute_address_id(self):
        for asset in self:
            if asset.site_id :
                asset.address_id = asset.site_id.address_id
            else :
                asset.address_id = asset.asset_address_id
    
    partner_id = fields.Many2one('res.partner', string='Customer', ondelete='restrict', help="Customer for this asset.")
    
    confirmed_lead_id = fields.Many2one('crm.lead', string='Confirmed Lead')
    candidate_lead_ids = fields.One2many('crm.lead', 'building_asset_id', string='Candidate Leads', domain=['|',('active','=',True),('active','=',False)])
    
    @api.onchange('confirmed_lead_id')
    def update_confirmed_lead_id(self):
        self.partner_id = self.confirmed_lead_id.partner_id
        self.state = 'sold'
    
    sale_order_ids = fields.One2many('sale.order', 'building_asset_id', string="Sale Orders", readonly=True)
    invoice_ids = fields.One2many('account.invoice','building_asset_id', string="Invoices", readonly=True) 
    
class SaleOrder(models.Model):
    '''Sale Order'''
    _inherit = "sale.order"
    
    building_site_id = fields.Many2one('construction.building_site', string='Building Site', related="building_asset_id.site_id",store=True)
    building_asset_id = fields.Many2one('construction.building_asset', string='Building Asset', ondelete='restrict')
    
    @api.onchange('state')
    def update_asset_state(self):
        if self.state == 'sent':
            self.building_asset_id.state = 'proposal'
            # TODO add to the candidate lead_ids
        if self.state == 'sale':
            self.building_asset_id.state = 'sold'
            self.confirmed_lead_id.id = self.opportunity_id.id
                
    @api.onchange('partner_id')
    def onchange_parter(self):
        if self.partner_id:
            asset_id = self.env['construction.building_asset'].search([('partner_id','=',self.partner_id.id)])
            if asset_id :
                self.building_asset_id = asset_id[0]
            
    @api.multi
    def _prepare_invoice(self):
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        invoice_vals['building_asset_id'] = self.building_asset_id.id or False
        return invoice_vals
        
    amount_outstanding = fields.Monetary(string='Outstanding Amount', store=True, readonly=True, compute='_amount_outstanding')
    amount_open = fields.Monetary(string='Open Amount', store=True, readonly=True, compute='_amount_outstanding')
        
    @api.depends('order_line.price_total','order_line.invoice_lines','invoice_ids.residual_signed')
    def _amount_outstanding(self):
        """
        Compute the outstanding amounts of the SO.
        """
        for order in self:
            amount_outstanding = 0.0
            amount_open = 0.0
            for line in order.order_line :
                amount_outstanding += line.price_subtotal * (line.product_uom_qty-line.qty_invoiced)
            for invoice_id in order.invoice_ids :
                amount_open += invoice_id.residual_signed
                    
            order.update({
                'amount_outstanding': order.pricelist_id.currency_id.round(amount_outstanding),
                'amount_open': order.pricelist_id.currency_id.round(amount_open),
            })
            
class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.multi
    def _prepare_invoice_line(self, qty):
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        if self.order_id.building_site_id :
            res.update({'account_analytic_id': self.order_id.building_site_id.analytic_account_id.id})
        return res
            
class CrmLean(models.Model):
    '''CRM Lead'''
    _inherit = "crm.lead"
    
    building_site_id = fields.Many2one('construction.building_site', string='Building Site', related="building_asset_id.site_id",store=True)
    building_asset_id = fields.Many2one('construction.building_asset', string='Building Asset', ondelete='restrict')
    
    @api.multi
    def _convert_opportunity_data(self, customer, team_id=False):
        res = super(CrmLean, self)._convert_opportunity_data(self, customer, team_id)
        res['building_asset_id'] = self.building_asset_id.id or False
    
class Invoice(models.Model):
    '''Invoice'''
    _inherit = 'account.invoice'
    
    building_site_id = fields.Many2one('construction.building_site', string='Building Site', related="building_asset_id.site_id",store=True)
    building_asset_id = fields.Many2one('construction.building_asset', string='Building Asset', ondelete='restrict')
    
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
