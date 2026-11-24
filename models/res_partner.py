# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ResPartner(models.Model):
    """Extending res.partner model to add extra fields and methods"""
    _inherit = "res.partner"

    vehicle_ids = fields.One2many('workshop.vehicle','vehicle_owner_id')
    vehicle_count = fields.Char("Vehicles",compute="_compute_vehicle_count")
    appointment_ids = fields.One2many('calendar.event','customer_id',string='Appointment')
    appointment_count = fields.Char(string='Appointment History', compute='_compute_appointment_count')
    job_order_ids = fields.One2many('workshop.job.order','customer_id',string='Job Orders')

    @api.depends('vehicle_ids')
    def _compute_vehicle_count(self):
        """Calculate vehicle count"""
        for record in self:
            record.vehicle_count = len(record.vehicle_ids)

    @api.depends('appointment_ids')
    def _compute_appointment_count(self):
        """Calculate Appointment count"""
        for record in self:
            record.appointment_count = len(record.appointment_ids)

    def action_vehicles_smart_button(self):
        """Vehicle Smart Button Function"""
        return {
            "name": _("Vehicles"),
            "type": "ir.actions.act_window",
            "res_model": "workshop.vehicle",
            "view_mode": "list",
            "domain": [('vehicle_owner_id','in',self.id)],
            "context" : {'create': False},
        }

    def action_appointment_history(self):
        """Appointment history Button Function"""
        return{
            'name': _('Appointments'),
            'type': 'ir.actions.act_window',
            'res_model': 'calendar.event',
            'view_mode': 'list,form',
            'domain': [('customer_id','in',self.id)],
        }