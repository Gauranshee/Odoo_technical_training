from odoo import models, fields

class ResUsers(models.Model):
    _inherit = "res.users"
    property_ids = fields.One2many('estate.property','salesperson_id', string='Properties',domain=[('state','=','new')])
    # we have used _inherit bcz res.users already exists ,we extend it do NOT create new table..Tis is called CLASSICAL MODEL INHERITANCE
    # One2many(target_model,inverse_field).....so estate_property=target model.....salesperson_id=inverse_field
    # DOMAIN show only available properties