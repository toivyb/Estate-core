
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
import random

ai_bp = Blueprint('ai_bp', __name__)

@ai_bp.route('/api/ai/lease-renewal-suggestion', methods=['POST'])
@jwt_required()
def lease_renewal_suggestion():
    data = request.json
    current_rent = float(data.get('current_rent', 0))
    on_time_ratio = float(data.get('on_time_ratio', 1.0))  # ratio between 0 and 1
    unit = data.get('unit', '')

    # Mock market adjustment (e.g. 3% yearly increase)
    market_adjustment = 1.03

    # Risk-adjustment
    if on_time_ratio < 0.8:
        suggested_rent = current_rent  # no raise for bad payment
        renewal_term = "Month-to-Month"
        notes = "Due to frequent late payments, recommend a flexible term."
    elif on_time_ratio < 0.95:
        suggested_rent = current_rent * market_adjustment
        renewal_term = "6 Months"
        notes = "Slightly increased rent due to occasional delays."
    else:
        suggested_rent = current_rent * (market_adjustment + 0.02)
        renewal_term = "12 Months"
        notes = "Good payment history. Recommend full term with minor increase."

    return jsonify({
        "unit": unit,
        "suggested_rent": round(suggested_rent, 2),
        "renewal_term": renewal_term,
        "notes": notes
    })
