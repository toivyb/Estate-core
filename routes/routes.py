from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from ..models import User
from ..utils.auth_utils import admin_required

routes_bp = Blueprint("routes", __name__, url_prefix="/api")

@routes_bp.route("/users", methods=["GET"])
@jwt_required()
@admin_required  # Only super_admins can access this
def get_all_users():
    users = User.query.all()
    user_list = [{
        "id": u.id,
        "email": u.email,
        "role": u.role
    } for u in users]
    return jsonify(user_list), 200
