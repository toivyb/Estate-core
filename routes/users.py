from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError

from estatecore_backend.models import db, User

users_bp = Blueprint("users", __name__)

def require_super_admin():
    claims = get_jwt()
    role = claims.get("role")
    if role != "super_admin":
        return jsonify(msg="Forbidden: super_admin only"), 403
    return None

@users_bp.get("/users")
@jwt_required()
def list_users():
    maybe_forbidden = require_super_admin()
    if maybe_forbidden:
        return maybe_forbidden

    users = User.query.order_by(User.id.asc()).all()
    return jsonify([
        {"id": u.id, "email": u.email, "role": u.role, "is_active": u.is_active}
        for u in users
    ])

@users_bp.post("/users")
@jwt_required()
def create_user():
    maybe_forbidden = require_super_admin()
    if maybe_forbidden:
        return maybe_forbidden

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = data.get("role") or "user"
    is_active = bool(data.get("is_active", True))

    if not email or not password:
        return jsonify(msg="email and password required"), 400

    user = User(
        email=email,
        password_hash=generate_password_hash(password),
        role=role,
        is_active=is_active,
    )
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(msg="email already exists"), 409

    return jsonify(id=user.id, email=user.email, role=user.role, is_active=user.is_active), 201

@users_bp.put("/users/<int:user_id>")
@jwt_required()
def update_user(user_id: int):
    maybe_forbidden = require_super_admin()
    if maybe_forbidden:
        return maybe_forbidden

    user = User.query.get_or_404(user_id)
    data = request.get_json(silent=True) or {}

    if "email" in data:
        new_email = (data.get("email") or "").strip().lower()
        if not new_email:
            return jsonify(msg="email cannot be empty"), 400
        user.email = new_email

    if "password" in data and data["password"]:
        user.password_hash = generate_password_hash(data["password"])

    if "role" in data and data["role"]:
        user.role = data["role"]

    if "is_active" in data:
        user.is_active = bool(data["is_active"])

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(msg="email already exists"), 409

    return jsonify(id=user.id, email=user.email, role=user.role, is_active=user.is_active)

@users_bp.delete("/users/<int:user_id>")
@jwt_required()
def delete_user(user_id: int):
    maybe_forbidden = require_super_admin()
    if maybe_forbidden:
        return maybe_forbidden

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return "", 204
