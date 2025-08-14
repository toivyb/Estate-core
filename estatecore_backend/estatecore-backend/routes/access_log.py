from flask import Blueprint, request, jsonify
from estatecore_backend import db
from estatecore_backend.models.access_attempt import AccessAttempt
from utils.auth import token_required

access_log = Blueprint('access_log', __name__)

@access_log.route('/api/access-attempt', methods=['POST'])
def log_access_attempt():
    data = request.json
    attempt = AccessAttempt(
        user_id=data.get('user_id'),
        gate_name=data['gate_name'],
        property_id=data['property_id'],
        result=data['result'],
        reason=data.get('reason', None)
    )
    db.session.add(attempt)
    db.session.commit()
    return jsonify({'message': 'Access attempt logged'}), 201

@access_log.route('/api/access-log/<int:property_id>', methods=['GET'])
@token_required
def get_access_log(current_user, property_id):
    attempts = AccessAttempt.query.filter_by(property_id=property_id).order_by(AccessAttempt.timestamp.desc()).limit(50).all()
    return jsonify([
        {
            'id': a.id,
            'user_id': a.user_id,
            'gate_name': a.gate_name,
            'result': a.result,
            'timestamp': a.timestamp.isoformat(),
            'reason': a.reason
        } for a in attempts
    ])