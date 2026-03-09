from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import date
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class EstateProperty(models.Model):
    _name = 'estate.property'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Real Estate Property'
    _order = "id desc"

    # -------------------------------------------------------------------------
    # Computed Fields
    # -------------------------------------------------------------------------

    @api.depends("offer_ids.price")
    def _compute_best_price(self):
        """Returns the highest offer price. Falls back to 0 if no offers exist."""
        for record in self:
            record.best_price = max(record.offer_ids.mapped('price') or [0])

    @api.depends('living_area', 'garden_area')
    def _compute_total_area(self):
        """Total area = living area + garden area."""
        for record in self:
            record.total_area = record.living_area + record.garden_area

    # -------------------------------------------------------------------------
    # Fields
    # -------------------------------------------------------------------------

    active = fields.Boolean(default=True)

    state = fields.Selection([
        ('new', 'New'),
        ('offer_received', 'Offer Received'),
        ('offer_accepted', 'Offer Accepted'),
        ('sold', 'Sold'),
        ('canceled', 'Canceled'),
    ], required=True, copy=False, default='new')

    # readonly=True: prevents users from editing the system-generated sequence code.
    seq_estate_property = fields.Char("Estate Code", readonly=True)

    name              = fields.Char(string='Title', required=True)
    description       = fields.Text(string='Description')
    best_price        = fields.Float(string='Best Price', compute='_compute_best_price')
    postcode          = fields.Char(string='Postcode')
    date_availability = fields.Date(
        string='Available From',
        copy=False,
        default=lambda self: fields.Date.today() + relativedelta(months=3)
    )
    expected_price    = fields.Float(string='Expected Price', required=True)
    selling_price     = fields.Float(string='Selling Price', readonly=True, copy=False)
    bedrooms          = fields.Integer(string='Bedrooms', default=2)
    living_area       = fields.Integer(string='Living Area')
    facades           = fields.Integer(string='Facades')
    garage            = fields.Boolean(string='Garage')
    garden            = fields.Boolean(string='Garden')
    garden_area       = fields.Integer(string='Garden Area (sqm)')
    garden_orientation = fields.Selection([
        ('north', 'North'),
        ('south', 'South'),
        ('east', 'East'),
        ('west', 'West'),
    ], string='Garden Orientation')

    total_area        = fields.Float(string='Total Area', compute='_compute_total_area')
    expiry_date       = fields.Date(string="Expiry Date")

    # Relational fields
    property_type_id  = fields.Many2one('estate.property.type', string='Property Type')
    offer_ids         = fields.One2many('estate.property.offer', 'property_id', string='Offers')
    tag_ids           = fields.Many2many('estate.property.tag', string='Tags')
    salesperson_id    = fields.Many2one('res.users', string='Salesperson')
    user_id           = fields.Many2one('res.users', string="Owner")

    # -------------------------------------------------------------------------
    # Onchange
    # -------------------------------------------------------------------------

    @api.onchange('garden')
    def _onchange_garden(self):
        """Reset garden area to 0 when the Garden checkbox is unchecked."""
        for estate in self:
            if not estate.garden:
                estate.garden_area = 0

    @api.onchange('date_availability')
    def _onchange_date_availability(self):
        """Warn the user if the selected availability date is in the past."""
        for estate in self:
            if estate.date_availability and estate.date_availability < fields.Date.today():
                return {
                    "warning": {
                        "title": "Warning",
                        "message": "Availability date is in the past"
                    }
                }

    # -------------------------------------------------------------------------
    # Action Buttons
    # -------------------------------------------------------------------------

    def action_sold(self):
        """Mark the property as Sold. Raises an error if it is already cancelled."""
        if self.state == 'canceled':
            raise UserError("Cancelled properties cannot be sold.")
        _logger.info("action_sold triggered for property ID: %s", self.id)
        self.state = 'sold'
        return True

    def action_cancelled(self):
        """
        Cancel the property.
        If called with context {'archive_on_cancel': True}, also archives the record
        (sets active=False so it is hidden from default views).
        """
        if self.state == 'sold':
            raise UserError("Sold properties cannot be cancelled.")
        self.state = 'canceled'
        if self.env.context.get('archive_on_cancel'):
            self.active = False
        return True

    # -------------------------------------------------------------------------
    # Constraints
    # -------------------------------------------------------------------------

    _sql_constraints = [
        ('check_expected_price', 'CHECK(expected_price > 0)',
         'Expected price must be positive.'),
        ('check_selling_price', 'CHECK(selling_price >= 0)',
         'Selling price must be positive.'),
    ]

    @api.constrains('selling_price')
    def _check_constraints(self):
        """
        Selling price must be at least 90% of the expected price.
        Only validated when selling_price > 0 to allow new/unsold records
        where selling_price has not been set yet.
        """
        for estate in self:
            if estate.selling_price > 0 and \
               estate.selling_price < estate.expected_price * 0.9:
                raise ValidationError(
                    "Selling price must be at least 90% of the expected price."
                )

    # -------------------------------------------------------------------------
    # CRUD Overrides
    # -------------------------------------------------------------------------

    def unlink(self):
        """Prevent deletion of properties that are not in New or Cancelled state."""
        for record in self:
            if record.state not in ('new', 'canceled'):
                raise UserError('Only New or Cancelled properties can be deleted.')
        return super().unlink()

    @api.model
    def create(self, vals):
        """Auto-assign the next sequence code (e.g. PROP0001) on every new property."""
        vals['seq_estate_property'] = self.env['ir.sequence'].next_by_code('estate.code')
        return super(EstateProperty, self).create(vals)

    # -------------------------------------------------------------------------
    # Scheduled Action (Cron) — Task 5: ir.config_parameter
    # -------------------------------------------------------------------------

    def _cron_mark_expired_properties(self):
        """
        Scheduled daily job: cancels properties whose expiry_date has passed.

        Uses ir.config_parameter to check a feature flag before running:
          - Key: estate.auto_expire_enabled  → set to 'True' to enable (default).
          - Key: estate.last_expire_cron_run → updated with today's date after each run.

        ir.config_parameter stores simple key-value settings in the database.
        get_param() reads a value; set_param() writes it.
        These can be inspected at Settings > Technical > Parameters > System Parameters.
        """
        # Read the feature flag. If not set, defaults to 'True' (enabled).
        auto_expire = self.env['ir.config_parameter'].sudo().get_param(
            'estate.auto_expire_enabled', default='True'
        )
        if auto_expire != 'True':
            _logger.info("Cron: auto-expire is disabled via system parameters. Skipping.")
            return

        today = date.today()
        properties = self.search([
            ('expiry_date', '<', today),
            ('state', 'not in', ['sold', 'canceled']),
        ])

        if properties:
            properties.write({'state': 'canceled'})
            _logger.info(
                "Cron: marked %d expired properties as Cancelled.", len(properties)
            )

        # Record the last execution date so admins can verify the cron ran successfully.
        self.env['ir.config_parameter'].sudo().set_param(
            'estate.last_expire_cron_run', str(today)
        )
