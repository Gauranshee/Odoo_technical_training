from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    property_reference = fields.Char(string="Property Reference")

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    # extend existing inventory model

    delivery_note = fields.Text(string="Delivery Note")
    delivery_note_no = fields.Char(string="Delivery Note No")




