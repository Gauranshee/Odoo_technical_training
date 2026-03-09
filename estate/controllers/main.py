import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class EstateAPI(http.Controller):
    """
    JSON API controller for the Estate module.

    Routes are registered by Odoo's HTTP layer when the module loads.
    auth='user' requires a valid session; use auth='public' only if
    unauthenticated access is explicitly required.
    """

    @http.route('/api/properties', type='json', auth='user', methods=['POST'])
    def get_properties(self):
        """
        Returns a list of all estate properties as JSON.

        Performance note:
          .mapped() iterates over an already-loaded recordset in Python —
          no extra SQL queries are issued compared to a manual for-loop.
          Both approaches are equivalent here because the recordset is fully
          loaded by search(). mapped() is preferred for readability.

        Logging:
          - INFO on success so operators can confirm the endpoint was hit.
          - ERROR on failure with exc_info=True to include the full traceback
            in server logs for easier debugging.
        """
        _logger.info("GET /api/properties called by user: %s", request.env.user.name)

        try:
            properties = request.env['estate.property'].search([])

            result = [{
                'name':           rec.name,
                'expected_price': rec.expected_price,
                'state':          rec.state,
            } for rec in properties]

            _logger.info(
                "GET /api/properties returned %d records successfully.", len(result)
            )
            return {'status': 'success', 'data': result, 'count': len(result)}

        except Exception as e:
            _logger.error(
                "GET /api/properties failed: %s", str(e), exc_info=True
            )
            return {'status': 'error', 'message': str(e)}
