from flask import Blueprint, jsonify
rev_bp = Blueprint('rev_bp', __name__)

@rev_bp.route('/api/revenue-leakage/<int:property_id>', methods=['GET'])
def revenue_leakage(property_id):
    # Dummy leakage data
    return jsonify({'leaks': [{'unit': 'A1', 'issue': 'Unpaid fees'}]})
