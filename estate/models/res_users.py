from odoo import models, fields

class ResUsers(models.Model):
    _inherit = "res.users"
    # One2many: links properties where this user is the salesperson.
    # domain: only shows properties in 'New' state (available for sale).
    # _inherit is used here because res.users already exists in Odoo core.
    # Classical inheritance extends the existing model without creating a new database table.
    property_ids = fields.One2many(
        'estate.property', 'salesperson_id',
        string='Properties',
        domain=[('state', '=', 'new')]
    )