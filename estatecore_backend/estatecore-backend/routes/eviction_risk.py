from flask import Blueprint, request, jsonify
from estatecore_backend import db
from estatecore_backend.models.eviction_risk import EvictionRisk
from utils.auth import token_required

eviction_risk = Blueprint('eviction_risk', __name__)

@eviction_risk.route('/api/eviction-risk/<int:tenant_id>', methods=['GET'])
@token_required
def get_risk(current_user, tenant_id):
    r = EvictionRisk.query.filter_by(tenant_id=tenant_id).order_by(EvictionRisk.created_at.desc()).first()
    return jsonify({
        "score": r.risk_score if r else None,
        "level": r.risk_level if r else "unknown"
    })