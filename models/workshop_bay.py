# -*- coding: utf-8 -*-
from odoo import models, fields, exceptions


class WorkshopBay(models.Model):
    """Used to define the bays available for work"""
    _name = "workshop.bay"
    _description = "Bay"
    _rec_name = 'bay_name'
    _inherit = ['mail.thread','mail.activity.mixin']

    bay_name = fields.Char(string='Name', copy=False, required=True)
    active = fields.Boolean("Archived", default=True)
    assigned_employee_id = fields.Many2one('hr.employee',
                                           string='Assigned Employee',
                                           tracking=True)
    bay_type = fields.Char(string="Type")
    bay_status = fields.Selection(string='Status',
                                  selection=[('free','Free'),('occupied','Occupied'),
                                             ('closed','Closed')],
                                  default='free', copy=False, tracking=True)
    ongoing_job_ids = fields.One2many('workshop.job.order','workshop_bay_id',
                                      string='Ongoing Job', copy=False, tracking=True,
                                      domain=[('job_status','=','in_progress')])
    supported_job_type_ids = fields.Many2many('workshop.job.type',
                                              string='Supported Job Types', required=True)

    def action_close_status(self):
        """Function for CLOSE status which checks if any work is in progress"""
        if self.ongoing_job_ids:
            raise exceptions.ValidationError("Work is already in progress")
        self.bay_status = 'closed'

    def action_reset_status(self):
        """Function for resetting status to free"""
        self.bay_status = 'free'