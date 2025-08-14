from flask import Blueprint, jsonify
from estatecore_backend import db
from estatecore_backend.models.revenue_leak import RevenueLeak
from utils.auth import token_required

leakage = Blueprint('leakage', __name__)

@leakage.route('/api/revenue-leakage/<int:property_id>', methods=['GET'])
@token_required
def get_leaks(current_user, property_id):
    records = RevenueLeak.query.filter_by(property_id=property_id).all()
    return jsonify([{
        "unit": r.unit,
        "issue": r.issue,
        "created_at": r.created_at.isoformat()
    } for r in records])