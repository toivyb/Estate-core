from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from .. import db
from ..models import MaintenanceRequest

bp = Blueprint("maintenance", __name__)

@bp.get("/maintenance")
@jwt_required()
def list_maintenance():
    items = MaintenanceRequest.query.order_by(MaintenanceRequest.created_at.desc()).all()
    return jsonify([{"id": m.id, "title": m.title, "status": m.status} for m in items])

@bp.post("/maintenance")
@jwt_required()
def create_request():
    data = request.get_json() or {}
    m = MaintenanceRequest(title=data.get("title",""), description=data.get("description",""))
    db.session.add(m); db.session.commit()
    return jsonify({"id": m.id})
