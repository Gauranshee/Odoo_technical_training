from odoo import fields, models, api
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError


class EstateOffer(models.Model):
    _name = 'estate.property.offer'
    _description = 'Offer made on a Real Estate Property'
    _order = "price desc"

    # -------------------------------------------------------------------------
    # Fields
    # -------------------------------------------------------------------------

    price      = fields.Float(string='Price')
    state      = fields.Selection([
        ('accepted', 'Accepted'),
        ('refused',  'Refused'),
    ], copy=False)

    partner_id       = fields.Many2one('res.partner', required=True, string='Buyer')
    property_id      = fields.Many2one('estate.property', required=True, string='Property')
    # related: pulls property_type_id from the linked property automatically.
    # store=True: persists the value in the DB so it can be filtered/grouped.
    property_type_id = fields.Many2one(
        related='property_id.property_type_id',
        store=True,
        string='Property Type'
    )

    validity = fields.Integer(string='Validity (days)', default=7)
    # compute: auto-calculates deadline from today + validity days.
    # inverse: if the user edits deadline directly, validity is recalculated to match.
    date_deadline = fields.Date(
        string="Deadline",
        compute='_compute_date_deadline',
        inverse='_inverse_date_deadline'
    )

    # -------------------------------------------------------------------------
    # Computed / Inverse
    # -------------------------------------------------------------------------

    @api.depends('create_date', 'validity')
    def _compute_date_deadline(self):
        """Deadline = today + validity days."""
        for offer in self:
            offer.date_deadline = fields.Date.today() + relativedelta(days=offer.validity)

    def _inverse_date_deadline(self):
        """When the user edits the deadline, recalculate validity in days."""
        for offer in self:
            offer.validity = (offer.date_deadline - fields.Date.today()).days

    # -------------------------------------------------------------------------
    # Action Buttons
    # -------------------------------------------------------------------------

    def action_accept(self):
        """Accept this offer: set state to accepted and update property selling price."""
        self.ensure_one()
        if "accepted" in self.property_id.offer_ids.mapped('state'):
            raise UserError("An offer has already been accepted for this property.")
        self.state = 'accepted'
        self.property_id.selling_price = self.price

    def action_refuse(self):
        """Refuse this offer: reset selling price on the property."""
        self.ensure_one()
        if self.state == 'refused':
            raise UserError("This offer has already been refused.")
        self.state = 'refused'
        self.property_id.selling_price = 0

    # -------------------------------------------------------------------------
    # Constraints
    # -------------------------------------------------------------------------

    _sql_constraints = [
        ('check_offer_price', 'CHECK(price > 0)', 'Offer price must be positive.'),
    ]

    # -------------------------------------------------------------------------
    # CRUD Overrides
    # -------------------------------------------------------------------------

    @api.model
    def create(self, vals):
        """
        On offer creation:
        1. Set the parent property state to 'Offer Received'.
        2. Reject the offer if it is lower than or equal to any existing offer.
        """
        property_rec = self.env['estate.property'].browse(vals.get('property_id'))
        property_rec.state = 'offer_received'
        existing_offers = property_rec.offer_ids.mapped('price')
        if existing_offers and vals.get('price', 0) < max(existing_offers):
            raise UserError(
                "The offer price must be higher than the current best offer (%.2f)."
                % max(existing_offers)
            )
        return super().create(vals)
