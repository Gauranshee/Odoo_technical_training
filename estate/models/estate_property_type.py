from odoo import fields, models


class EstatePropertyType(models.Model):
    _name = 'estate.property.type'
    _description = 'Property type'
    _order = 'sequence,name'

    sequence = fields.Integer(string='Sequence',default=10)
    name = fields.Char(string='Property Type', required=True)

    property_ids = fields.One2many('estate.property', 'property_type_id', string='Properties')
    offer_ids = fields.One2many('estate.property.offer','property_type_id',string='Offers')
    offer_count = fields.Integer(compute='_compute_offer_count')

    def _compute_offer_count(self):
        for rec in self:
            rec.offer_count=len(rec.offer_ids)

    _sql_constraints =[
        ('unique_property_type_name','UNIQUE(name)','Property type name must be unique')]
