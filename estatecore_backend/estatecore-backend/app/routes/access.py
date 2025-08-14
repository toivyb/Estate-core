
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from .. import db
from ..models.access import AccessLog

bp = Blueprint('access', __name__)

@bp.post('/access/check')
def access_check():
    data = request.get_json() or {}
    allow = data.get('allow', True)
    log = AccessLog(property_id=data.get('property_id'), user_id=data.get('user_id'), event='allow' if allow else 'deny', reason=data.get('reason'))
    db.session.add(log)
    db.session.commit()
    return jsonify({'result': 'allow' if allow else 'deny'})
