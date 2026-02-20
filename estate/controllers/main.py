from odoo import http
from odoo.http import request

class EstateAPI(http.Controller):

    @http.route('/api/properties', type='json', auth='public', methods=['POST'])
    def get_properties(self):
        properties = request.env['estate.property'].sudo().search([])
        result = []

        for rec in properties:
            result.append({
                'name': rec.name,
                'expected_price': rec.expected_price,
                'state': rec.state,
            })

        return result

