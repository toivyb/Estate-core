from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from ..models import User
from .. import db

bp = Blueprint("api", __name__)

@bp.get("/ping")
def ping(): return jsonify(ok=True), 200

@bp.post("/login")
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    if not email or not password: return jsonify(msg="missing credentials"), 400
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password): return jsonify(msg="bad credentials"), 401
    token = create_access_token(identity=user.as_identity())
    return jsonify(access_token=token), 200

@bp.get("/me")
@jwt_required()
def me(): return jsonify(user=get_jwt_identity()), 200
