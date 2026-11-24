from odoo import models, fields, api, exceptions
from odoo.tools import html2plaintext


class CalendarEvent(models.Model):
    """Calendar for appointment booking"""
    _inherit = 'calendar.event'

    allday = fields.Boolean(default=True)
    customer_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    customer_phone = fields.Char(string="Phone", related='customer_id.phone')
    vehicle_id = fields.Many2one('workshop.vehicle', string='Vehicle',
                                 domain="[('vehicle_owner_id','=',customer_id)] if customer_id else []")
    job_order_ids = fields.One2many('workshop.job.order','appointment_id',string='Job Order',copy=False)
    appointment_confirm = fields.Boolean(default=False, tracking=True, copy=False)
    job_order_count = fields.Char(string='Job Orders', compute='_compute_job_count')
    customer_notes = fields.Text(string='Customer Notes', compute='_compute_customer_notes')
    company_id = fields.Many2one('res.company', string='Company')
    mail_sent = fields.Boolean(string='Mail Sent',default=False)


    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        """Adds customer phone number if available and resets vehicle selection if needed"""
        if self.vehicle_id.vehicle_owner_id != self.customer_id:
            self.vehicle_id, self.customer_phone = None, None
        if self.customer_id:
            self.customer_phone = self.customer_id.phone

    @api.onchange('vehicle_id')
    def _onchange_vehicle_id(self):
        """Customer auto selected according to vehicle"""
        if self.vehicle_id:
            self.customer_id = self.vehicle_id.vehicle_owner_id

    @api.depends('job_order_ids')
    def _compute_job_count(self):
        """Computes number of job orders linked"""
        for record in self:
            record.job_order_count = len(record.job_order_ids)

    @api.depends('notes')
    def _compute_customer_notes(self):
        """Converts notes HTML field to text"""
        for record in self:
            record.customer_notes = html2plaintext(record.notes or '')

    def action_confirm_appointment(self):
        """Change appointment status to confirmed"""
        self.appointment_confirm = True
        self.is_draft = False

    def action_cancel_appointment(self):
        """Cancel appointment allowed if no job orders are present"""
        if self.job_order_ids:
            raise exceptions.ValidationError('Delete Job Orders before cancelling appointments')
        else:
            self.appointment_confirm = False
            self.is_draft = True

    def action_create_job_order(self):
        """Create job order directly from the appointment"""
        return {
            'name': 'Job Order',
            'type': 'ir.actions.act_window',
            'res_model': 'workshop.job.order',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_customer_id': self.customer_id.id,
                'default_customer_phone_number': self.customer_phone,
                'default_vehicle_id': self.vehicle_id.id,
                'default_job_date': self.start_date,
                'default_appointment_id': self.id,
                'default_customer_notes': self.customer_notes,
            }
        }

    def action_show_job_orders(self):
        """Show all the job orders linked"""
        return{
            'name': 'Job Orders',
            'type' : 'ir.actions.act_window',
            'res_model': 'workshop.job.order',
            'view_mode': 'list,form',
            'domain': [('appointment_id','in',self.id)]
        }

    @api.model
    def send_appointment_reminder(self):
        """Mail for appointment reminder for next day"""
        template= self.env.ref('workshop.mail_template_appointment_reminder')
        records  = self.env['calendar.event'].search([('appointment_confirm','=',True)])
        for record in records:
            if fields.Date.subtract(record.start_date,days=1) == fields.Date.today():
                template.send_mail(record.id,force_send=True)

