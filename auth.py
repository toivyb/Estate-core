# C:\Users\FSSP\estatecore_project\estatecore_backend\auth.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, jwt_required, get_jwt_identity, get_jwt
)

bp = Blueprint("auth", __name__)

# demo user store; replace with real DB lookup
USERS = {
    "admin@example.com": {"password": "admin123", "role": "super_admin", "id": 1}
}

@bp.post("/login")
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password")

    user = USERS.get(email)
    if not user or user["password"] != password:
        return jsonify({"msg": "Bad credentials"}), 401

    # IMPORTANT: identity MUST be a STRING (PyJWT wants 'sub' as str)
    access_token = create_access_token(
        identity=email,                           # <- string
        additional_claims={"role": user["role"], "uid": str(user["id"])}
    )
    return jsonify(access_token=access_token), 200

@bp.get("/me")
@jwt_required()
def me():
    email = get_jwt_identity()   # <- string you set above
    claims = get_jwt()           # includes 'role', 'uid' we added
    return jsonify(email=email, role=claims.get("role"), uid=claims.get("uid")), 200
