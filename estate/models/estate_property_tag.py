from odoo import fields, models


class EstatePropertyTag(models.Model):
    _name = 'estate.property.tag'
    _description = 'Property Tag'
    _order = 'name'

    name  = fields.Char(string='Name', required=True)
    # Integer: used by the many2many_tags widget to render each tag in a distinct colour.
    color = fields.Integer(string='Color Index')

    _sql_constraints = [
        ('unique_tag_name', 'UNIQUE(name)', 'Tag name must be unique.'),
    ]
