from flask import Blueprint, request, jsonify
from estatecore_backend import db
from estatecore_backend.models.payment import Payment
from utils.auth import token_required

payment_bp = Blueprint('payment_bp', __name__)

@payment_bp.route('/api/pay', methods=['POST'])
@token_required
def pay(current_user):
    data = request.json
    p = Payment(
        tenant_id=current_user.id,
        amount=data['amount'],
        status='pending'
    )
    db.session.add(p)
    db.session.commit()
    return jsonify({"status": "created"})