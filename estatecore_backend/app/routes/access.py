from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from ..models import AccessLog

bp = Blueprint("access", __name__)

@bp.get("/access/logs")
@jwt_required()
def logs():
    items = AccessLog.query.order_by(AccessLog.ts.desc()).limit(50).all()
    return jsonify([{"user_email": a.user_email, "door": a.door, "status": a.status, "ts": a.ts.isoformat()} for a in items])
