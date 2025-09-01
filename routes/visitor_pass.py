from flask import Blueprint, request, jsonify
from estatecore_backend import db
from estatecore_backend.models.visitor_pass import VisitorPass
from utils.auth import token_required
from datetime import datetime, timedelta
import secrets

visitor_pass_bp = Blueprint('visitor_pass_bp', __name__)

@visitor_pass_bp.route('/api/visitor-pass', methods=['POST'])
@token_required
def generate_pass(current_user):
    data = request.json
    code = secrets.token_urlsafe(6)
    pass_entry = VisitorPass(
        property_id=data['property_id'],
        generated_by=current_user.id,
        code=code,
        expires_at=datetime.utcnow() + timedelta(hours=int(data.get('valid_hours', 4)))
    )
    db.session.add(pass_entry)
    db.session.commit()
    return jsonify({'code': code, 'expires_at': pass_entry.expires_at.isoformat()}), 201

@visitor_pass_bp.route('/api/visitor-pass/validate', methods=['POST'])
def validate_pass():
    data = request.json
    record = VisitorPass.query.filter_by(code=data['code']).first()
    if not record or record.expires_at < datetime.utcnow():
        return jsonify({'valid': False}), 400
    return jsonify({'valid': True, 'property_id': record.property_id})