from flask import Blueprint, request, session
from .. import db
from ..models import User

auth_bp = Blueprint("auth", __name__)

@auth_bp.post("/login")
def login():
    data = request.get_json(force=True)
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return {"error": "Invalid credentials"}, 401
    session["user_id"] = user.id
    session["role"] = user.role
    return {"id": user.id, "email": user.email, "role": user.role}

@auth_bp.post("/logout")
def logout():
    session.clear()
    return {"ok": True}

@auth_bp.get("/me")
def me():
    uid = session.get("user_id")
    if not uid:
        return {"user": None}, 200
    user = User.query.get(uid)
    if not user:
        return {"user": None}, 200
    return {"id": user.id, "email": user.email, "role": user.role}