from flask import Blueprint, request, jsonify

payment_bp = Blueprint('payment_bp', __name__, url_prefix="/api")

@payment_bp.route('/payments', methods=['GET'])
def list_payments():
    """Get all payments - simplified version"""
    sample_payments = [
        {
            "id": 1,
            "tenant_id": 101,
            "amount": "1200.00",
            "status": "completed",
            "payment_method": "card",
            "created_at": "2024-09-01T10:00:00"
        },
        {
            "id": 2,
            "tenant_id": 102,
            "amount": "1500.00",
            "status": "pending",
            "payment_method": "bank_transfer",
            "created_at": "2024-09-02T14:30:00"
        }
    ]
    return jsonify({"payments": sample_payments})

@payment_bp.route('/payments', methods=['POST'])
def create_payment():
    """Create a new payment - simplified version"""
    data = request.json or {}
    new_payment = {
        "id": 999,  # Mock ID
        "tenant_id": data.get('tenant_id'),
        "amount": data.get('amount'),
        "payment_method": data.get('payment_method', 'card'),
        "status": 'pending',
        "created_at": "2024-09-03T12:00:00"
    }
    return jsonify(new_payment), 201

@payment_bp.route('/pay', methods=['POST'])
def pay():
    """Simple payment endpoint for backward compatibility"""
    data = request.json or {}
    return jsonify({"status": "created", "payment_id": 999})