from odoo import models, api
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        for order in self:
            if not order.partner_id.vat:
                raise ValidationError(
                    "Cannot confirm Sale Order. Customer GST number is missing."
                )

        return super(SaleOrder, self).action_confirm()
