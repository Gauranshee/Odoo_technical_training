from odoo import fields, models
import logging

_logger = logging.getLogger(__name__)


class EstateCron(models.Model):
    _name = 'estate.cron'
    _description = 'Estate Cron Automation'

    def daily_cron_job(self):
        """
        Scheduled daily job: sets all CRM leads to high priority (priority=1).

        Performance note:
          records.write({...}) issues a SINGLE bulk UPDATE SQL statement for all
          matched records, regardless of count. This is far more efficient than
          calling rec.write() inside a loop, which would issue one UPDATE per record
          (N+1 problem).
        """
        try:
            _logger.info("Daily Cron Job Started")

            # search([]) fetches all CRM lead records.
            records = self.env['crm.lead'].search([])

            if not records:
                _logger.info("Daily Cron Job: no CRM leads found. Nothing to update.")
                return

            # Bulk write: single SQL UPDATE for all records — avoids N+1 queries.
            records.write({'priority': '1'})

            _logger.info(
                "Daily Cron Job Executed Successfully — %d leads updated to high priority.",
                len(records)
            )

        except Exception as e:
            _logger.error("Daily Cron Job Failed: %s", str(e), exc_info=True)
