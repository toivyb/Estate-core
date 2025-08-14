from flask import Blueprint, jsonify
cash_flow_bp = Blueprint('cash_flow_bp', __name__)

@cash_flow_bp.route('/api/cash-flow/<int:property_id>', methods=['GET'])
def get_cash_flow(property_id):
    # Dummy projection logic
    return jsonify({'next_month_projection': 1234.56})
