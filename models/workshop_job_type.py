# -*- coding: utf-8 -*-
from odoo import models,fields


class WorkshopJobType(models.Model):
    """List all the job types available"""
    _name = 'workshop.job.type'
    _description = 'Job Type'
    _rec_name = 'job_type_name'

    job_type_name = fields.Char('Job Type Name')
    active = fields.Boolean("Archive", default=True)
