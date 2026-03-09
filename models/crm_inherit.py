from odoo import models, fields, api
from odoo.exceptions import ValidationError

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    source_reference = fields.Char(string="Source Reference")

    @api.constrains('expected_revenue')
    def _check_expected_revenue(self):
        for record in self:
            if record.expected_revenue <= 0:
                raise ValidationError("Expected Revenue must be greater than 0.")

    @api.constrains('stage_id', 'source_reference')
    def _check_source_reference_when_won(self):
        for record in self:
            # stage ko check kar rahe hain
            if record.stage_id.is_won and not record.source_reference:
                raise ValidationError(
                    "Source Reference is mandatory when the lead is Won."
                )

