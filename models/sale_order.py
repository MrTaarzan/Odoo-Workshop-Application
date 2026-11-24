# -*- coding: utf-8 -*-
from odoo import models, fields
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    """Extending Sale order to include job order and vehicle"""
    _inherit = 'sale.order'

    job_order_id = fields.Many2one('workshop.job.order','Job Order', ondelete='restrict', copy=False)
    vehicle_id = fields.Many2one('workshop.vehicle', related="job_order_id.vehicle_id")

    def _prepare_invoice(self):
        """Function for creating an invoice after work is done"""
        if self.job_order_id.job_status == 'done':
            invoice_vals = super(SaleOrder,self)._prepare_invoice()
            invoice_vals['job_order_id'] = self.job_order_id.id
            self.job_order_id.job_status = 'invoiced'
            return invoice_vals
        else:
            raise ValidationError("Cannot create Invoice without completing the work")

    def action_confirm(self):
        """Confirm button action"""
        self.job_order_id.job_status = 'confirmed'
        return super().action_confirm()
