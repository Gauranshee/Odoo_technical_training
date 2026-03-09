import logging

# 'requests' is a third-party Python library for making HTTP calls.
# It is included in Odoo's requirements.txt so it is always available.
import requests

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

# Base URL of the dummy REST API used for testing external integrations.
# JSONPlaceholder is a free, public fake API that returns predictable sample data.
DUMMY_API_URL = 'https://jsonplaceholder.typicode.com/posts'


class EstateApiData(models.Model):
    """
    Task 6: External API Integration.

    Stores records fetched from an external REST API.
    Integration pattern:
      1. Send an HTTP GET request to the external API.
      2. Validate the response status code.
      3. Parse the JSON payload.
      4. Clear stale records and persist fresh data to the database.
      5. Log each step and handle specific error types explicitly.
    """

    _name = 'estate.api.data'
    _description = 'External API Data'
    _order = 'post_id asc'

    # Integer: stores the post ID returned by the API (whole number, no decimals).
    post_id = fields.Integer(string='Post ID', readonly=True)

    # The user ID from the API response — not a Many2one since it is an external identifier.
    api_user_id = fields.Integer(string='API User ID', readonly=True)

    # Char: single-line text — appropriate for short values like titles.
    title = fields.Char(string='Title', readonly=True)

    # Text: multi-line text — appropriate for longer content bodies.
    body = fields.Text(string='Content', readonly=True)

    # Datetime: stores both date and time of the fetch operation.
    # default=fields.Datetime.now automatically records the current timestamp on create.
    fetch_date = fields.Datetime(
        string='Fetched On',
        readonly=True,
        default=fields.Datetime.now
    )

    @api.model
    def fetch_from_api(self):
        """
        Fetches posts from the external dummy API and stores them in this model.

        @api.model decorator: this method operates at the model level (class method),
        not on a specific record. 'self' here has no record IDs — it represents
        the model class itself.

        Error handling:
        - Specific exception types are caught first (ConnectionError, Timeout, HTTPError)
          to provide targeted, informative log messages.
        - A generic Exception catch-all handles unexpected failures.
        - All exceptions are re-raised so the caller can decide how to handle them.
        """
        try:
            _logger.info("External API fetch initiated. URL: %s", DUMMY_API_URL)

            # timeout=10: if the server does not respond within 10 seconds,
            # a Timeout exception is raised. Always set a timeout to prevent
            # indefinite hangs in production environments.
            response = requests.get(DUMMY_API_URL, timeout=10)

            # raise_for_status() converts HTTP error responses (4xx, 5xx) into
            # Python exceptions, enabling consistent error handling.
            response.raise_for_status()

            # .json() deserialises the response body from a JSON string into
            # a Python list of dictionaries.
            data = response.json()
            _logger.info("API response received. Total available records: %d", len(data))

            # Remove all previously stored records before inserting fresh data.
            # search([]) returns all records; unlink() issues a DELETE query.
            old_records = self.search([])
            old_records.unlink()
            _logger.info("Previous records cleared. Storing new data.")

            # Limit to the first 10 records to keep the demo data manageable.
            created_count = 0
            for post in data[:10]:
                self.create({
                    'post_id': post.get('id', 0),
                    'api_user_id': post.get('userId', 0),
                    'title': post.get('title', ''),
                    'body': post.get('body', ''),
                    # 'fetch_date' is populated automatically via its default value.
                })
                created_count += 1

            _logger.info(
                "External API fetch completed successfully. %d records stored.",
                created_count
            )

        except requests.exceptions.ConnectionError as e:
            _logger.error(
                "API fetch failed: connection error. "
                "Verify network connectivity and the API URL. Details: %s", str(e)
            )
            raise

        except requests.exceptions.Timeout as e:
            _logger.error(
                "API fetch failed: request timed out after 10 seconds. "
                "The server may be slow or unreachable. Details: %s", str(e)
            )
            raise

        except requests.exceptions.HTTPError as e:
            _logger.error(
                "API fetch failed: HTTP error response received (4xx/5xx). Details: %s", str(e)
            )
            raise

        except requests.exceptions.RequestException as e:
            _logger.error(
                "API fetch failed: a general requests error occurred. Details: %s", str(e)
            )
            raise

        except Exception as e:
            _logger.error(
                "API fetch failed: unexpected error during data processing. Details: %s", str(e)
            )
            raise
