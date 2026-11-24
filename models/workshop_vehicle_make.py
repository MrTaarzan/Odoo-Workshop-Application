# -*- coding: utf-8 -*-
from odoo import models, fields


class VehicleMake(models.Model):
    """Vehicle Manufacturer List"""
    _name = 'workshop.vehicle.make'
    _description = "Manufacturer"
    _rec_name = 'vehicle_make'

    vehicle_make = fields.Char('Manufacturer')
    active = fields.Boolean("Archive", default=True)