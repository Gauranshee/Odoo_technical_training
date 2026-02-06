from odoo import fields,models,api
from dateutil.relativedelta import relativedelta


class EstateOffer(models.Model):
    _name='estate.property.offer'
    _description = 'Offer made for real estate'

    price = fields.Float()
    status = fields.Selection([
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



