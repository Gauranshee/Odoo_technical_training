from odoo import fields,models,api
from dateutil.relativedelta import relativedelta

from odoo.exceptions import UserError


class EstateOffer(models.Model):
    _name='estate.property.offer'
    _description = 'Offer made for real estate'
    _order = "price desc"

    price = fields.Float()
    state= fields.Selection([
        ('accepted', 'Accepted'),
        ('refused', 'Refused'),
    ],
    copy=False,
    )
    partner_id = fields.Many2one('res.partner',required=True)
    property_id = fields.Many2one('estate.property',required=True)
    property_type_id = fields.Many2one(related='property_id.property_type_id',store=True,string='Property Type')

    validity = fields.Integer(string='Validity',default=7)
    date_deadline = fields.Date(string="Deadline",compute='_compute_date_deadline',inverse='_inverse_date_deadline')
    # date_deadline compute--auto calculate hogi user manually nahi likhega
    # inverse function---if user changes deadline VALIDITY will change automatically

    @api.depends('create_date','validity')
    def _compute_date_deadline(self):
        for property in self:
            property.date_deadline = fields.date.today() + relativedelta(days=property.validity)


    def _inverse_date_deadline(self):
        for property in self:
            property.validity = (property.date_deadline - fields.Date.today()).days



    def action_accept(self):
        self.ensure_one()
        if "accepted" in self.property_id.offer_ids.mapped('state'):
            raise UserError("Property already sold")
        self.state= "accepted"
        self.property_id.selling_price = self.price

    def action_refuse(self):
        self.ensure_one()
        if "refused" in self.property_id.offer_ids.mapped('state'):
            raise UserError("Offer already refused")
        self.state= "refused"
        self.property_id.selling_price = 0

    _sql_constraints =[
        ('check_offer_price', 'CHECK(price>0)', 'Offer price must be positive')]


    def create(self,vals):
        property_rec = self.env['estate.property'].browse(vals.get('property_id'))
        property_rec.state='offer_received'
        existing_offer=property_rec.offer_ids.mapped('price')
        if existing_offer and vals.get('price') < max(existing_offer):
            raise UserError("Offer must be higher than existing offer")
        return super().create(vals)





