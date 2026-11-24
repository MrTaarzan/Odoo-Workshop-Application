# -*- coding: utf-8 -*-
from odoo import models, fields, api


class WorkshopVehicle(models.Model):
    """Vehicle details"""
    _name = 'workshop.vehicle'
    _description = 'Vehicle'
    _rec_name = 'license_plate'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    license_plate = fields.Char(string='License Plate', required=True,
                                tracking=True, copy=False)
    vin_num = fields.Char(string='VIN', tracking=True, copy=False, required=True)
    vehicle_model = fields.Char(string='Model', tracking=True)
    model_year = fields.Char(string='Model Year')
    vehicle_color = fields.Char(string='Vehicle Color')
    odometer_reading = fields.Integer(string='Odometer Reading', tracking=True)
    active = fields.Boolean('Active', default=True)
    job_order_count = fields.Char(string='Job Orders', compute='_compute_job_order_count')
    vehicle_make = fields.Many2one('workshop.vehicle.make',string='Make', tracking=True)
    vehicle_owner_id = fields.Many2one('res.partner',
                                       string='Vehicle Owner', tracking=True,
                                       required=True)
    job_order_ids = fields.One2many('workshop.job.order', 'vehicle_id', string="Job order")
    _check_license_plate = models.Constraint(
        'UNIQUE(license_plate)', 'License Plate must be unique'
    )
    _check_vin_num = models.Constraint(
        'UNIQUE(vin_num)','VIN should be unique'
    )
    _check_odometer_reading = models.Constraint(
        'CHECK(odometer_reading > 0)', 'Odometer reading should be positive'
    )


    @api.depends('job_order_ids')
    def _compute_job_order_count(self):
        """To compute number of job orders for a vehicle"""
        for record in self:
            record.job_order_count = len(record.job_order_ids)

    def action_job_history(self):
        """Vehicle Job history action"""
        return {
            'name': 'Job Orders',
            'type': 'ir.actions.act_window',
            'res_model': 'workshop.job.order',
            'view_mode': 'list,form',
            'views': [
                (self.env.ref('workshop.workshop_job_order_sec_list').id, 'list'),
                (self.env.ref('workshop.workshop_job_order_form').id, 'form')
            ],
            'domain': [('vehicle_id','in', self.id)],
            'context': {'create': False},
        }
