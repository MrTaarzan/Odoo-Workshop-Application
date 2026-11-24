# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AccountMove(models.Model):
    """Extending Invoice to include job order and vehicle"""
    _inherit = 'account.move'

    job_order_id = fields.Many2one('workshop.job.order', string="Job Order", ondelete='restrict')

    def _get_invoice_in_payment_state(self):
        """Get the status of payment and update it"""
        self.job_order_id.payment_state = 'paid'
        return super()._get_invoice_in_payment_state()
