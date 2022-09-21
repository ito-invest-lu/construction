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
    _inherit = 'construction.building_asset'

    project_id = fields.One2many('project.project','building_asset_id', string="Project", readonly=True) 
    
    def open_or_create_project(self):
        self.ensure_one()
        if not self.project_id :
            self.create_project()
        return {
            'name': 'Project',
            'view_mode': 'form',
            'res_model': 'project.project',
            'type': 'ir.actions.act_window',
            'res_id': self.project_id.id,
            'context': self.env.context,
        }
    
    def create_project(self):
        project_template = self.env['project.project'].search([('name','=','Template'),('active','=',False)])
        self.project_id = project_template.copy()
        self.project_id.write({
            'name' : self.name,
            'partner_id' : self.partner_id.id,
            'building_asset_id' : self.id,
            'active' : True,
        })
    
class Project(models.Model):
    '''Project'''
    _inherit = 'project.project'
    
    building_asset_id = fields.Many2one('construction.building_asset', string='Building Asset', ondelete='restrict')
    
    parent_id = fields.Many2one('project.project', string='Parent Project', ondelete='restrict')
    child_ids = fields.One2many('project.project', 'parent_id', string='Children Projects')
    
    parent_cost_pct = fields.Float(string="Parent pourcentage of costs")

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_('Error ! You cannot create recursive projects.'))
            
    on_going_task_ids = fields.Many2many('project.task', string="OnGoing Tasks", compute='_compute_on_going_task_ids')

    def _compute_on_going_task_ids(self):
        for rec in self :
            on_going_stage_id = self.env['ir.model.data']._xmlid_to_res_id('construction_project.project_stage_ongoing')
            for project in rec:
                project.on_going_task_ids = project.task_ids.filtered(lambda t: t.stage_id == on_going_stage_id)

    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id.id)
    company_currency = fields.Many2one(string='Currency', related='company_id.currency_id', readonly=True, relation="res.currency")

    budget = fields.Monetary(string="Budget", currency_field='company_currency', compute='_compute_amounts')
    is_on_budget = fields.Boolean(string="Is On Budget", compute="_compute_amounts")
    
    purchase_amount = fields.Monetary(string="Purchase Amount", currency_field='company_currency', compute='_compute_amounts')
    working_hours = fields.Float(string="Working Hours", compute='_compute_amounts')
    total_amount = fields.Monetary(string="Total Amount", currency_field='company_currency', compute='_compute_amounts')
    
    @api.depends('task_ids.budget','task_ids.purchase_amount','task_ids.working_hours')
    def _compute_amounts(self):
        for project in self:
            project.budget = sum(project.task_ids.mapped('budget'))
            project.purchase_amount = sum(project.task_ids.mapped('purchase_amount'))
            project.working_hours = sum(project.task_ids.mapped('working_hours'))
            project.total_amount = sum(project.task_ids.mapped('total_amount'))
            project.is_on_budget = project.budget >= project.total_amount

class Task(models.Model):
    '''Task'''
    _inherit = 'project.task'
    
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id.id)
    company_currency = fields.Many2one(string='Currency', related='company_id.currency_id', readonly=True, relation="res.currency")
    
    budget = fields.Monetary(string="Budget", currency_field='company_currency')
    is_on_budget = fields.Boolean(compute="_compute_total", string="Is On Budget", store=True)
    
    purchase_amount = fields.Monetary(string="Purchase Amount", currency_field='company_currency')
    working_hours = fields.Float(string="Working Hours")
    total_amount = fields.Monetary(compute="_compute_total", string="Total Amount", currency_field='company_currency', store=True)
    
    analytic_line_id = fields.Many2one('account.analytic.line', string='Analytic Line for Purchases', ondelete='restrict', readonly=True)
    
    @api.depends('budget','purchase_amount','working_hours')
    def _compute_total(self):
        for rec in self :
            working_hours_price = self.env['ir.config_parameter'].sudo().get_param('construction.hour_price', default=50)
            total_amount = rec.purchase_amount + rec.working_hours * working_hours_price
            if rec.analytic_line_id :
                rec.analytic_line_id.write({
                    'unit_amount' : rec.working_hours,
                    'amount' : total_amount,
                })
            else :
                self.env['account.analytic.line'].create({
                    'name': self.name,
                    'account_id': rec.project_id.analytic_account_id.id,
                    'task_id': rec.id,
                    'unit_amount': rec.working_hours,
                    'amount': total_amount,
                })
            rec.total_amount = total_amount
            rec.is_on_budget = rec.budget >= rec.total_amount

    @api.onchange('budget','purchase_amount','working_hours','is_on_budget')
    def _onchange_is_on_budget(self):
        if self.budget > 0 :
            if self.budget * 0.80 >= self.total_amount :
                self.color = 10
            elif self.budget >= self.total_amount :
                self.color = 2
            else :
                self.color = 1

    def set_to_not_started(self):
        self.write ({
            'stage_id' :  self.env['ir.model.data']._xmlid_to_res_id('construction_project.project_stage_not_started').id
        })

    def set_to_ongoing(self):
        self.write ({
            'stage_id' :  self.env['ir.model.data']._xmlid_to_res_id('construction_project.project_stage_ongoing').id
        })
        
    def set_to_done(self):
        self.write ({
            'stage_id' :  self.env['ir.model.data']._xmlid_to_res_id('construction_project.project_stage_finished').id
        })
        
# class SaleOrderForcastMonth(models.Model):
#     _name = 'sale.order.line.forecast_month'
    
#     _order = 'year, month'
    
#     name = fields.Char(compute='_compute_name')
    
#     show_in_kanban = fields.Boolean(string='Show in Kanban')
    
#     company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.user.company_id.id)
#     company_currency = fields.Many2one(string='Currency', related='company_id.currency_id', readonly=True, relation="res.currency")
    
#     sale_amount_delivered = fields.Monetary(compute='_compute_sale_amount_total', string="Sum of Delivered Lines", help="Untaxed Total of Delivered Lines", currency_field='company_currency')
#     sale_amount_total = fields.Monetary(compute='_compute_sale_amount_total', string="Sum of Lines", help="Untaxed Total of Planned Lines", currency_field='company_currency')
#     sale_number = fields.Integer(compute='_compute_sale_amount_total', string="Number of Quotations")
    
#     order_line_ids = fields.One2many('sale.order.line', 'forecast_month_id', string='Lines')

#     @api.depends('order_line_ids')
#     def _compute_sale_amount_total(self):
#         for month in self:
#             total = 0.0
#             total_d = 0.0
#             nbr = 0
#             company_currency = month.company_currency or self.env.user.company_id.currency_id
#             for line in month.order_line_ids:
#                 nbr += 1
#                 total += line.currency_id.compute(line.price_subtotal, company_currency)
#                 if line.qty_delivered > 0:
#                     total_d += line.currency_id.compute(line.price_subtotal, company_currency)
#             month.sale_amount_delivered = total_d
#             month.sale_amount_total = total
#             month.sale_number = nbr
    
#     def _compute_name(self):
#         self.name = '%s-%s' % (self.year,self.month)
    
#     year = fields.Selection([('2018', '2018'), ('2019', '2019'), ('2020', '2020'), ('2021', '2021'), ('2022', '2022')],string='Year')
#     month = fields.Selection([('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'),('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'),('9', '9'), ('10', '10'), ('11', '11'), ('12', '12')],string='Month')

# class SaleOrderLine(models.Model):
#     _inherit = "sale.order.line"

#     forecast_month_id = fields.Many2one('sale.order.line.forecast_month', string='Assigned to Month', track_visibility='onchange')
    
#     kanban_state = fields.Selection([
#         ('normal', 'Grey'),
#         ('done', 'Green'),
#         ('blocked', 'Red')], string='Kanban State',
#         copy=False, default='normal', required=True,
#         help="A task's kanban state indicates special situations affecting it:\n"
#              " * Grey is the default situation\n"
#              " * Red indicates something is preventing the progress of this task\n"
#              " * Green indicates the task is ready to be pulled to the next stage")
#     kanban_state_label = fields.Char(compute='_compute_kanban_state_label', string='Kanban State', track_visibility='onchange')
    
#     @api.depends('kanban_state')
#     def _compute_kanban_state_label(self):
#         for line in self:
#             if line.kanban_state == 'normal':
#                 line.kanban_state_label = 'planned'
#             elif line.kanban_state == 'blocked':
#                 line.kanban_state_label = 'blocked'
#             else:
#                 line.kanban_state_label = 'done'
    
#     forecast_status = fields.Selection([('planned', 'Planned'), ('danger', 'Danger'), ('invoiced', 'Invoiced'), ('ongoing', 'On going'), ('to invoice', 'To invoice')], string='Forecast Status', stroe=True, compute='_compute_forecast_status', track_visibility='onchange')
    
#     @api.depends('invoice_status','kanban_state')
#     def _compute_forecast_status(self):
#         for line in self:
#             if line.invoice_status == 'invoiced' or line.invoice_status == 'upselling' :
#                 line.forecast_status = 'invoiced'
#             elif line.invoice_status == 'to invoice':
#                 line.forecast_status = 'to invoice'
#             elif line.kanban_state == 'normal':
#                 line.forecast_status = 'planned'
#             elif line.kanban_state == 'blocked':
#                 line.kanban_state_label = 'danger'
#             else:
#                 line.kanban_state_label = 'ongoing'
    
#     priority = fields.Selection([('0', 'Very Low'), ('1', 'Low'), ('2', 'Normal'), ('3', 'High')], string='Priority')
#     color = fields.Integer(string='Color Index')