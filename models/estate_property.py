

from odoo import models,fields,api
from dateutil.relativedelta import relativedelta
from datetime import date
from odoo.exceptions import UserError, ValidationError
import logging
_logger = logging.getLogger(__name__)


class EstateProperty(models.Model):
    _name = 'estate.property'
    _inherit = ['mail.thread','mail.activity.mixin']
    _description = 'Real Estate Property'
    _order = "id desc"


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

    seq_estate_property = fields.Char("Estate Code")
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

    salesperson_id = fields.Many2one('res.users',string='Salesperson')

    total_area = fields.Float(string='Total Area',compute='_compute_total_area')

    user_id = fields.Many2one('res.users', string="Owner")

    my_custom_field = fields.Char(string="Custom Info")

    expiry_date = fields.Date(string="Expiry Date")

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
            if estate.date_availability and estate.date_availability < fields.Date.today():
                return{
                    "warning": {
                        "title": "Warning",
                        "message": "Availability date is in the past"
                    }
                }
# adding button cancelled and sold to estate property

    def action_sold(self):
        if self.state == 'cancelled':
            raise UserError("Cancelled Properties cannot be sold")
        _logger.info("Button action_sold triggered for record ID: %s", self.id)
        self.state = 'sold'
        return True

    def action_cancelled(self):
        if self.state == 'sold':
            raise UserError("Sold properties cannot be canceled")
        self.state = 'canceled'
        if self.env.context.get('archive_on_cancel'):
            self.active = False
        return True

   #--------- CONSTRAINTS CHAPTER---------

    _sql_constraints =[
        ('check_expected_price','CHECK(expected_price>0)','Expected price must be positive'),
         ('check_selling_price','CHECK(selling_price>=0)','Selling price must be positive')
    ]

    @api.constrains('selling_price')
    def _check_constraints(self):
        for estate in self:
            if estate.selling_price < estate.expected_price * 0.9:
                raise ValidationError("Selling price must be at least 90% of expected price")

            # ------------------CRUD Inheritance-----------------


    def unlink(self):
        for record in self:
            if record.state not in ('new', 'canceled'):
                raise UserError('You cannot delete this property!')
        return super().unlink()

    @api.model
    def create(self, vals):
        print("Estate Property create vals",vals)
        vals["seq_estate_property"]= self.env['ir.sequence'].next_by_code('estate.code')
        return super(EstateProperty, self).create(vals)


    # Create a cron job

    def _cron_mark_expired_properties(self):
        today = date.today()
        properties = self.search([
            ('expiry_date', '<', today),
            ('state', '!=', 'sold')
        ])
        properties.write({'state': 'sold'})





