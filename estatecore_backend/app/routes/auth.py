from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from ..models import User
from .. import db

bp = Blueprint("auth", __name__)

@bp.post("/login")
def login():
    data = request.get_json(force=True)
    email = data.get("email","").strip().lower()
    password = data.get("password","")
    user = User.query.filter_by(email=email).first()
    if not user or not user.is_active or not user.check_password(password):
        return jsonify({"msg":"Login failed"}), 401
    token = create_access_token(identity={"id": user.id, "role": user.role, "email": user.email})
    return jsonify(access_token=token, user={"email": user.email, "role": user.role})
