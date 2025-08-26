# app/routes/auth.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from app import db
from app.models import User

bp = Blueprint("auth", __name__)

@bp.post("/login")
def login():
    data = request.get_json(force=True) or {}
    email = data.get("email") or data.get("username")
    password = data.get("password") or ""
    if not email or not password:
        return jsonify({"msg": "email and password required"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or getattr(user, "is_active", True) is False or not user.check_password(password):
        return jsonify({"msg": "bad credentials"}), 401

    claims = {"email": user.email, "role": getattr(user, "role", None)}
    access  = create_access_token(identity=str(user.id), additional_claims=claims)
    refresh = create_refresh_token(identity=str(user.id))
    return jsonify(access_token=access, refresh_token=refresh, user=claims), 200

@bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    ident = get_jwt_identity()
    return jsonify(access_token=create_access_token(identity=ident)), 200

@bp.get("/me")
@jwt_required()
def me():
    ident = get_jwt_identity()
    # If earlier tokens used dict identities, accept them
    if isinstance(ident, dict):
        return jsonify(ident), 200
    try:
        uid = int(ident)
    except Exception:
        return jsonify({"msg": "invalid identity"}), 400
    u = User.query.get(uid)
    if not u:
        return jsonify({"msg": "user not found"}), 404
    return jsonify({"id": u.id, "email": u.email, "role": getattr(u, "role", None)}), 200