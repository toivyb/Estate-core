from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from .models import db, User, Rent, Maintenance

api_bp = Blueprint("api", __name__)

# Example: Dashboard endpoint
@api_bp.route("/dashboard", methods=["GET"])
@jwt_required()
def dashboard():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = {
        "welcome": f"Welcome {user.email}",
        "rent_count": Rent.query.count(),
        "maintenance_count": Maintenance.query.count()
    }
    return jsonify(data), 200
