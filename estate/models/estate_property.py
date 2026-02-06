from odoo import models,fields,api
from dateutil.relativedelta import relativedelta
from datetime import date

class EstateProperty(models.Model):
    _name = 'estate.property'
    _description = 'Real Estate Property'


    @api.depends("offer_ids.price")
    def _compute_best_price(self):
        for record in self:
            record.best_price = max(record.offer_ids.mapped('price')or[0])
# uses[0] bcz,agr offer empty hue toh error nahi aayega


    active=fields.Boolean(default=True)
    state=fields.Selection([
        ('new', 'New'),
        ('offer_received', 'Offer Received'),
        ('offer_accepted', 'Offer Accepted'),
        ('sold', 'Sold'),
        ('canceled', 'Canceled'),
    ],

    required=True,
    copy=False,
    default='new',)


    name = fields.Char(string='Title',required=True)
    description = fields.Text(string='Description')
    best_price = fields.Float(string='Best Price',compute='_compute_best_price')
    postcode = fields.Char(string='Postcode')
    date_availability = fields.Date(string= 'Available From',copy=False,default=lambda self:fields.Date.today()+relativedelta(months=3))
    expected_price = fields.Float(string='Expected Price',required=True)
    selling_price = fields.Float(string='Selling Price',readonly=True,copy=False)
    bedrooms = fields.Integer(string='Bedrooms',default=2)
    living_area = fields.Integer(string='Living Area')
    facades = fields.Integer(string='Facades')
    garage = fields.Boolean(string='Garage')
    garden = fields.Boolean(string='Garden')
    garden_area = fields.Integer(string='Garden Area (sqm)')
    garden_orientation = fields.Selection([
        ('north', 'North'),
        ('south', 'South'),
        ('east', 'East'),
        ('west', 'West'),
    ],
        string='Garden Orientation'
    )

    property_type_id = fields.Many2one('estate.property.type',string='Property Type')

    offer_ids = fields.One2many('estate.property.offer','property_id',string='Offers')

    tag_ids = fields.Many2many('estate.property.tag',string='Tags')

# field computation
    best_offer = fields.Float(string='Best Offer',compute='_compute_best_price')

    total_area = fields.Float(string='Total Area',compute='_compute_total_area')

    @api.depends('living_area','garden_area')
    def _compute_total_area(self):
        for record in self:
            record.total_area = record.living_area + record.garden_area

    # using onchange field for garden and date availability
    @api.onchange('garden')
    def _onchange_garden(self):
        for estate in self:
            if not estate.garden:
                estate.garden_area = 0


    @api.onchange('date_availability')
    def _onchange_date_availability(self):
        for estate in self:
            return{
                "warning": {
                    "title": "Warning",
                    "message": "Availability date is in the past"
                }
            }
