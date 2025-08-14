from flask import Blueprint, jsonify
from utils.auth import token_required

leakage = Blueprint('leakage', __name__)

@leakage.route('/api/revenue-leakage/<int:property_id>', methods=['GET'])
@token_required
def leakage_report(current_user, property_id):
    return jsonify({
        "property_id": property_id,
        "leaks": [
            {"unit": "A1", "issue": "Under market rent"},
            {"unit": "C3", "issue": "No late fee applied"}
        ]
    })