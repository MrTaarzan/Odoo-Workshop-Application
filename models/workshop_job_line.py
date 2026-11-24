# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions


class WorkshopJobLine(models.Model):
    """Product lines and prices used to record products used or sold"""
    _name = "workshop.job.line"
    _description = "Job Line"

    job_order_id = fields.Many2one('workshop.job.order')
    product_id = fields.Many2one('product.product', required=True)
    quantity = fields.Float(string="Quantity")
    unit_price = fields.Float(string="Unit Price")
    company_id = fields.Many2one('res.company', store=True, copy=False,
                                 string="Company",
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency', related='company_id.currency_id',
                                 default=lambda
                                 self: self.env.company.currency_id.id)
    line_subtotal = fields.Monetary(string="Sub Total", compute="_compute_line_subtotal" ,readonly=True)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Assign the price of product automatically when product is selected"""
        if self.product_id:
            self.unit_price = self.product_id.lst_price
            self.quantity = 1.0

    @api.depends('quantity','unit_price')
    def _compute_line_subtotal(self):
        """Automatically compute subtotal price of each line"""
        for record in self:
            record.line_subtotal = record.unit_price*record.quantity

    @api.onchange('quantity')
    def _onchange_quantity(self):
        """Check quantity is not less than 1"""
        if self.quantity<1 and self.product_id:
            raise exceptions.ValidationError("Quantity cannot be less than 1")