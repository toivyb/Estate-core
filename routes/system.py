from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from estatecore_backend.models import User

system_bp = Blueprint("system", __name__)

@system_bp.route("/api/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "db": True}), 200

@system_bp.route("/api/me", methods=["GET"])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404
    return jsonify({
        "id": user.id,
        "email": user.email,
        "role": user.role
    }), 200
