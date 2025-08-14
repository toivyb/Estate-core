from flask import Blueprint, request, jsonify
from estatecore_backend import db
from estatecore_backend.models.lease_renewal import LeaseRenewal
from utils.auth import token_required
from datetime import datetime

lease_renewal = Blueprint('lease_renewal', __name__)

@lease_renewal.route('/api/lease-renewals', methods=['POST'])
@token_required
def create_renewal(current_user):
    data = request.json
    renewal = LeaseRenewal(
        tenant_id=data['tenant_id'],
        property_id=data['property_id'],
        suggested_months=data['suggested_months'],
        suggested_rent_increase=data['suggested_rent_increase']
    )
    db.session.add(renewal)
    db.session.commit()
    return jsonify({"message": "Lease renewal suggestion saved."})

@lease_renewal.route('/api/lease-renewals/<int:tenant_id>', methods=['GET'])
@token_required
def get_renewals(current_user, tenant_id):
    records = LeaseRenewal.query.filter_by(tenant_id=tenant_id).all()
    return jsonify([{
        "months": r.suggested_months,
        "increase": r.suggested_rent_increase,
        "created_at": r.created_at.isoformat()
    } for r in records])