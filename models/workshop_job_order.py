# -*- coding: utf-8 -*-
from odoo import models, fields, api,  exceptions, _
from odoo.orm.commands import Command


class WorkshopJobOrder(models.Model):
    """Used to list all the work orders"""
    _name = 'workshop.job.order'
    _description = 'Job Order'
    _rec_name = 'reference_number'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'reference_number desc'

    # === FIELDS === #
    reference_number = fields.Char('Reference Number', default=lambda self: _('Draft'),
                                   readonly=True, copy=False)
    customer_phone_number = fields.Char(string='Customer Phone')
    odometer_reading = fields.Integer("Odometer Reading", related="vehicle_id.odometer_reading",
                                      readonly=False)
    job_date = fields.Date(string='Job Date', default= fields.Date.context_today,required=True)
    warranty_status = fields.Boolean(string='Under-Warranty')
    job_status = fields.Selection(
        string='Job Status',
        selection=[('draft','Draft'),('quotation','Quotation'),
                   ('confirmed','Confirmed'),('in_progress','In Progress'),
                   ('done','Done'),('invoiced','Invoiced')],
        default='draft', tracking=True, copy=False
    )
    customer_notes = fields.Text(string="Customer's reported issue")
    repair_instructions = fields.Html(
        string='Repair Instructions',
        sanitize=True,
        sanitize_tags=True,
        strip_style=False
    )
    total_amount = fields.Monetary(string='Total Amount', readonly=True, compute="_compute_total_amount", store=True)
    sale_order_count = fields.Char("Sale Orders", compute="_compute_sale_order_count")
    invoice_count = fields.Char("Invoices", compute="_compute_invoice_count")
    job_type = fields.Char("Job Type", related='job_type_id.job_type_name', store=True)
    delivery_status = fields.Char("Delivery Status",readonly=True, copy=False, default='Pending')
    is_delivered = fields.Boolean("Delivered", default=False, copy=False)
    payment_state = fields.Selection([('paid','Paid'),('not_paid','Not Paid')],default='not_paid', copy=False)
    active = fields.Boolean("Archive", default=True)
    appointment_count= fields.Char(default='1', string='Appointment count')
    mail_sent = fields.Boolean(default=False)

    # === Many2one Fields === #
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  related='company_id.currency_id',
                                  default=lambda self: self.env.company.currency_id.id)
    company_id = fields.Many2one('res.company', store=True, copy=False,
                                 string="Company",
                                 default=lambda self: self.env.company)
    customer_id = fields.Many2one('res.partner', string='Customer Name', required=True)
    vehicle_id = fields.Many2one('workshop.vehicle','Vehicle',
                                 ondelete='restrict',required=True,
                                 domain="[('vehicle_owner_id','=',customer_id)] if customer_id else []")
    workshop_bay_id = fields.Many2one('workshop.bay', string='Work Bay',
                                      tracking=True,required=True,
                                      domain="[('supported_job_type_ids','in',job_type_id),"
                                             "('bay_status' ,'not in', ['closed'])] ")
    job_type_id = fields.Many2one('workshop.job.type',string="Job Type", required=True)
    appointment_id = fields.Many2one('calendar.event', string='Appointment',
                                     domain="[('appointment_confirm','=', True)] + ([('customer_id','=',customer_id)] if customer_id else [])",
                                     ondelete='restrict')

    # === One2many Fields === #
    job_line_ids = fields.One2many('workshop.job.line', 'job_order_id',
                                   string='Order Lines')
    sale_order_ids = fields.One2many('sale.order','job_order_id')
    invoice_ids = fields.One2many('account.move','job_order_id')

    # === Many2many Fields === #
    mechanic_ids = fields.Many2many('hr.employee',string='Mechanics',
                                    tracking=True,required=True)
    vehicle_image_ids = fields.Many2many('ir.attachment', string="Upload Vehicle Images")

    # === CRUD METHODS ===#
    @api.model_create_multi
    def create(self, vals_list):
        """Method to auto add reference number as a sequence"""
        for vals in vals_list:
            if vals.get('reference_number', _('Draft')) == _('Draft'):
                vals['reference_number'] = self.env['ir.sequence'].next_by_code('workshop.job.order')
        return super(WorkshopJobOrder, self).create(vals_list)

    @api.ondelete(at_uninstall=False)
    def _ondelete_job_order(self):
        """Restrict deletion of record if work is in progress"""
        for record in self:
            if record.sale_order_ids:
                raise exceptions.ValidationError("Remove Quotations to Delete record")
            if record.invoice_ids:
                raise exceptions.ValidationError("Remove Incoice to Delete record")

    # === ONCHANGE METHODS ===#
    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        """Adds customer phone number if available and resets vehicle selection if needed"""
        if self.vehicle_id.vehicle_owner_id != self.customer_id:
            self.vehicle_id, self.customer_phone_number = None, None
        if self.customer_id:
            self.customer_phone_number = self.customer_id.phone
        if self.appointment_id.customer_id != self.customer_id :
            self.appointment_id = None

    @api.onchange('vehicle_id')
    def _onchange_vehicle_id(self):
        """Customer auto selected according to vehicle"""
        if self.vehicle_id:
            self.customer_id = self.vehicle_id.vehicle_owner_id
        if self.appointment_id.vehicle_id != self.vehicle_id:
            self.appointment_id = None

    @api.onchange('job_type_id')
    def _onchange_job_type_id(self):
        """Reset Workshop bay whenever job type is changed"""
        self.workshop_bay_id = None

    @api.onchange('odometer_reading')
    def _onchange_odometer_reading(self):
        """Check if current reading is less than previous reading"""
        if self.odometer_reading < self.vehicle_id.odometer_reading:
            raise exceptions.ValidationError("Odometer reading cannot be less than current value")

    @api.onchange('appointment_id')
    def _onchange_appointment_id(self):
        """Data from appointment automatically filled"""
        if self.appointment_id:
            self.customer_id = self.appointment_id.customer_id
            self.vehicle_id = self.appointment_id.vehicle_id
            self.customer_notes = self.appointment_id.customer_notes

    #== COMPUTE METHODS ==#
    @api.depends('sale_order_ids')
    def _compute_sale_order_count(self):
        """Compute number of Sale Orders """
        for record in self:
            record.sale_order_count = len(record.sale_order_ids)

    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        """Compute number of Invoices """
        for record in self:
            record.invoice_count = len(record.invoice_ids)

    @api.depends('job_line_ids')
    def _compute_total_amount(self):
        """Calculate the total amount whenever products are added"""
        for record in self:
            record.total_amount = sum(record.job_line_ids.mapped('line_subtotal'))

    #== BUTTON ACTIONS ==#
    def action_job_confirmed(self):
        """Change job status to confirmed when CONFIRM button is clicked"""
        if self.sale_order_ids:
            self.sale_order_ids.action_confirm()
        elif self.job_line_ids:
            self.job_status = 'confirmed'
        else:
            raise exceptions.ValidationError("Add required Order lines before Confirming the Job Order")

    def action_reset_to_draft(self):
        """Action for RESET TO DRAFT button and change the bay status accordingly"""
        self.job_status = 'draft'
        if self.sale_order_ids:
            self.sale_order_ids._unlink_except_draft_or_cancel()
            self.sale_order_ids.unlink()
        for record in self.workshop_bay_id.ongoing_job_ids:
            if record.job_status == 'in_progress':
                self.sudo().workshop_bay_id.bay_status = 'occupied'
                return
        self.sudo().workshop_bay_id.bay_status = 'free'

    def action_start_work(self):
        """Action for START WORK button and restrict if bay is already occupied"""
        for record in self.workshop_bay_id:
            if record.sudo().bay_status == 'occupied':
                raise exceptions.ValidationError('This Bay is already occupied')
            else:
                self.job_status = 'in_progress'
                self.sudo().workshop_bay_id.bay_status = 'occupied'

    def action_mark_as_done(self):
        """Action for MARK AS DONE button and change bay status to free"""
        self.sale_order_ids._action_cancel()
        self.sale_order_ids.action_draft()
        order_lines =[Command.clear()]+[
            Command.create({
                'product_id' : record.product_id.id,
                'product_uom_qty': record.quantity,
                'price_unit': record.unit_price,
            })
            for record in self.job_line_ids
        ]
        self.sale_order_ids.write({
            'order_line': order_lines,
        })
        self.sale_order_ids.action_confirm()
        self.sudo().workshop_bay_id.bay_status = 'free'
        self.job_status = 'done'

    def action_create_quotation(self):
        """Action for Creating quotation"""
        if self.job_line_ids:
            sale_order_id = self.prepare_sale_order()
            self.job_status = 'quotation'

            return {
                'name':_("Sale Order"),
                'type': 'ir.actions.act_window',
                'res_model': 'sale.order',
                'view_mode': 'form',
                'res_id': sale_order_id.id,
                'target': 'current',
            }
        else:
            raise exceptions.ValidationError("Add required Order lines before creating a Quotation")

    def action_create_invoice(self):
        """Action for creating Invoice"""
        if self.sale_order_ids:
            sale_order = self.env['sale.order'].search([('job_order_id','=',self.id)])
            if sale_order.state != 'sale':
                sale_order.action_confirm()
            invoice = sale_order._create_invoices()
            self.job_status = 'invoiced'
            return {
                'name': _("Invoice"),
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'view_mode': 'form',
                'res_id': invoice.id,
                'target': 'current',
            }
        else:
            sale_order_id = self.prepare_sale_order()
            sale_order_id.action_confirm()
            self.job_status = 'done'
            invoice = sale_order_id._create_invoices()
            self.job_status = 'invoiced'
            return {
                'name': _("Invoice"),
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'view_mode': 'form',
                'res_id': invoice.id,
                'target': 'current',
            }

    def action_show_saleorders(self):
        """Action for all sale orders smart button"""
        return {
            "name": _("Sale Orders"),
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "view_mode": "form",
            'res_id': self.sale_order_ids.id,
            "context": {'create': False},
        }

    def action_show_invoices(self):
        """Action for all invoices smart button"""
        return {
            "name": _("Invoices"),
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "view_mode": "form",
            'res_id': self.invoice_ids.id,
            "context": {'create': False},
        }

    def action_delivered(self):
        """Action for Changing Delivery Status"""
        self.delivery_status = 'Delivered'
        self.is_delivered = True

    def action_show_appointment(self):
        """Show all appointments button action"""
        return{
            'name': 'Appointment',
            'type': 'ir.actions.act_window',
            'res_model': 'calendar.event',
            'view_mode': 'form',
            'res_id': self.appointment_id.id,
            'context': {'create': False},

        }
    #== OTHER METHODS ==#
    def prepare_sale_order(self):
        """Method for creating the job lines"""
        order_lines = [
            Command.create({
                'product_id' : record.product_id.id,
                'product_uom_qty': record.quantity,
                'price_unit' : record.unit_price,
            })
            for record in self.job_line_ids
        ]
        sale_order_id = self.env['sale.order'].create(
            {'job_order_id': self.id,
             'partner_id': self.customer_id.id,
             'order_line': order_lines,
             })
        return sale_order_id

    def automated_action_job_done(self):
        """Automated Action that will send a mail when job status is done"""
        template = self.env.ref('workshop.mail_template_work_done')
        for record in self:
            record.activity_schedule(
                'mail.mail_activity_data_todo',
                 summary='Follow up for Payment',
                 user_id = record.env.user.id)
            template.send_mail(record.id, force_send=True)

    @api.model
    def send_pickup_reminder_mail(self):
        """Mail will be sent after work done for pickup"""
        template = self.env.ref('workshop.mail_template_pickup_reminder')
        records = self.env['workshop.job.order'].search([
            ('job_status','in',['done','invoiced']),('delivery_status','=','Pending')
        ])
        for record in records:
            template.send_mail(record.id, force_send=True)