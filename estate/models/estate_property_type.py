from odoo import fields, models, api


class EstatePropertyType(models.Model):
    _name = 'estate.property.type'
    _description = 'Property Type'
    _order = 'sequence, name'

    sequence   = fields.Integer(string='Sequence', default=10)
    name       = fields.Char(string='Property Type', required=True)

    property_ids = fields.One2many('estate.property', 'property_type_id', string='Properties')
    offer_ids    = fields.One2many('estate.property.offer', 'property_type_id', string='Offers')

    # store=False (default): recomputed on demand, not persisted in the DB.
    offer_count  = fields.Integer(string='Offer Count', compute='_compute_offer_count')

    @api.depends('offer_ids')
    def _compute_offer_count(self):
        """
        Count offers per property type using read_group() for performance.

        Why read_group() instead of len(self.offer_ids)?
          - len(offer_ids) loads every offer record into memory (full ORM objects)
            just to count them — wasteful when there are many offers.
          - read_group() issues a single SELECT COUNT(*) GROUP BY query at the
            database level, returning only the count — no records are loaded.
          This pattern is the Odoo standard for computing count fields efficiently.
        """
        # read_group returns: [{'property_type_id': (id, name), 'property_type_id_count': N}, ...]
        offer_data = self.env['estate.property.offer'].read_group(
            domain=[('property_type_id', 'in', self.ids)],
            fields=['property_type_id'],
            groupby=['property_type_id'],
        )
        # Build a lookup dict: {type_id: count}
        count_map = {row['property_type_id'][0]: row['property_type_id_count']
                     for row in offer_data}

        for rec in self:
            rec.offer_count = count_map.get(rec.id, 0)

    _sql_constraints = [
        ('unique_property_type_name', 'UNIQUE(name)',
         'Property type name must be unique.'),
    ]
