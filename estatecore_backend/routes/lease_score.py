from flask import Blueprint, request, jsonify
from estatecore_backend import db
from estatecore_backend.models.lease_score import LeaseScore
from utils.auth import token_required

lease_score = Blueprint('lease_score', __name__)

@lease_score.route('/api/lease-score', methods=['POST'])
@token_required
def score_lease(current_user):
    data = request.json
    score = min(100, max(0, 80 + (data.get("credit_score", 600) - 600) / 10 - data.get("late_payments", 0) * 5))
    reason = "AI score based on credit and rent history"
    record = LeaseScore(
        tenant_id=data["tenant_id"],
        property_id=data["property_id"],
        score=score,
        reason=reason
    )
    db.session.add(record)
    db.session.commit()
    return jsonify({"score": score, "reason": reason}), 201

@lease_score.route('/api/lease-score/<int:tenant_id>', methods=['GET'])
@token_required
def get_score(current_user, tenant_id):
    scores = LeaseScore.query.filter_by(tenant_id=tenant_id).order_by(LeaseScore.created_at.desc()).all()
    return jsonify([
        {
            "score": s.score,
            "reason": s.reason,
            "created_at": s.created_at.isoformat()
        } for s in scores
    ])