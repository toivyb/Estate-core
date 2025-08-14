from flask import Blueprint, request, jsonify
from estatecore_backend import db
from estatecore_backend.models.cash_flow import CashFlow
from utils.auth import token_required

cash_flow = Blueprint('cash_flow', __name__)

@cash_flow.route('/api/cash-flow/<int:property_id>', methods=['GET'])
@token_required
def get_cash_flow(current_user, property_id):
    records = CashFlow.query.filter_by(property_id=property_id).all()
    return jsonify([
        {
            "income": r.projected_income,
            "expense": r.projected_expense,
            "date": r.projection_date.isoformat()
        } for r in records
    ])