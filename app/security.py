# app/security.py
from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt

def roles_required(*allowed):
    """Usage: @roles_required("admin")"""
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()  # access token claims
            # identity stored under "sub" (dict with role) or fallback to claim "role"
            sub = claims.get("sub") or {}
            role = None
            if isinstance(sub, dict):
                role = sub.get("role")
            if not role:
                role = claims.get("role")
            if role not in allowed:
                return jsonify({"msg": "forbidden"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return deco
