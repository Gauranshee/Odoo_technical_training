from odoo import fields, models
import logging

_logger = logging.getLogger(__name__)

class EstateCron(models.Model):
    _name = 'estate.cron'
    _description = 'Estate Cron Automation'

    def daily_cron_job(self):
        try:
            records=self.env['crm.lead'].search[()]
            _logger.info("Daily Cron Job Started")

            for rec in records:
                rec.write({'priority':'1'})

            _logger.info("Daily Cron Job Executed Successfully")

        except Exception as e:
            _logger.error("Daily Cron Job Failed: %s", str(e))



