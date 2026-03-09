from odoo import models, fields


class SaleOrderPropertyRef(models.Model):
    """Extends sale.order with a property reference field for cross-module traceability."""
    _inherit = 'sale.order'

    property_reference = fields.Char(string="Property Reference")


class StockPicking(models.Model):
    """Extends stock.picking with a delivery note number for estate delivery documentation."""
    _inherit = 'stock.picking'

    delivery_note_no = fields.Char(string="Delivery Note No")
