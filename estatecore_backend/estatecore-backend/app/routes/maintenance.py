
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from .. import db
from ..models.maintenance import MaintenanceRequest, MaintenanceComment

bp = Blueprint('maintenance', __name__)

@bp.get('/maintenance')
@jwt_required()
def list_requests():
    items = []
    for m in MaintenanceRequest.query.limit(500).all():
        items.append({'id': m.id, 'title': m.title, 'status': m.status})
    return jsonify(items)

@bp.post('/maintenance')
@jwt_required()
def create_request():
    data = request.get_json() or {}
    m = MaintenanceRequest(**data)
    db.session.add(m)
    db.session.commit()
    return {'id': m.id}

@bp.post('/maintenance/<int:mid>/comment')
@jwt_required()
def add_comment(mid):
    m = MaintenanceRequest.query.get_or_404(mid)
    body = request.get_json().get('body','')
    c = MaintenanceComment(request=m, body=body)
    db.session.add(c)
    db.session.commit()
    return {'ok': True}
