from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from ..decorators import require_roles
from ..models.user import UserRole

bp = Blueprint("admin", __name__)

@bp.get("/admin/ping")
@jwt_required()
@require_roles(UserRole.super_admin.value, UserRole.property_admin.value)
def admin_ping():
    return jsonify({"ok": True, "scope": "admin"})
