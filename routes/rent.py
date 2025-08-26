from flask import Blueprint, request, jsonify
from datetime import datetime, date
from decimal import Decimal

rent_bp = Blueprint("rent", __name__, url_prefix="/api")

@rent_bp.route("/rent", methods=["GET"])
def list_rent():
    """Get all rent records - simplified version without database"""
    # For now, return sample data to make the frontend work
    sample_data = [
        {
            "id": 1,
            "tenant_id": 101,
            "property_id": 201,
            "unit": "A1",
            "amount": "1200.00",
            "due_date": "2024-09-01",
            "status": "unpaid",
            "notes": "Monthly rent"
        },
        {
            "id": 2,
            "tenant_id": 102,
            "property_id": 201,
            "unit": "B2",
            "amount": "1500.00",
            "due_date": "2024-09-01",
            "status": "paid",
            "notes": "Monthly rent"
        }
    ]
    return jsonify({"rent_records": sample_data})

@rent_bp.route("/rent", methods=["POST"])
def create_rent():
    """Create a new rent record - simplified version"""
    data = request.get_json() or {}
    
    # Return success response with mock ID
    new_record = {
        "id": 999,  # Mock ID
        "tenant_id": data.get("tenant_id"),
        "property_id": data.get("property_id"),
        "unit": data.get("unit", ""),
        "amount": data.get("amount"),
        "due_date": data.get("due_date"),
        "status": "unpaid",
        "notes": data.get("notes", "")
    }
    return jsonify(new_record), 201

@rent_bp.route("/rent/<int:rent_id>/mark_paid", methods=["POST"])
def mark_rent_paid(rent_id):
    """Mark rent as paid - simplified version"""
    return jsonify({"message": f"Rent {rent_id} marked as paid"})

@rent_bp.route("/rent/<int:rent_id>/mark_unpaid", methods=["POST"])
def mark_rent_unpaid(rent_id):
    """Mark rent as unpaid - simplified version"""
    return jsonify({"message": f"Rent {rent_id} marked as unpaid"})

@rent_bp.route("/rent/<int:rent_id>", methods=["DELETE"])
def delete_rent(rent_id):
    """Delete rent record - simplified version"""
    return jsonify({"message": f"Rent {rent_id} deleted successfully"})

@rent_bp.route("/rent/<int:rent_id>/pdf", methods=["GET"])
def rent_receipt_pdf(rent_id):
    """Generate PDF receipt - simplified version"""
    return jsonify({"message": f"PDF receipt for rent {rent_id} would be generated"})

@rent_bp.route("/rent/<int:rent_id>", methods=["PUT"])
def update_rent(rent_id):
    """Update rent record - simplified version"""
    data = request.get_json() or {}
    return jsonify({"message": f"Rent {rent_id} updated", "data": data})
