
from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt

def _get_role():
    verify_jwt_in_request()
    claims = get_jwt() or {}
    role = claims.get("role")
    if not role and "roles" in claims and isinstance(claims["roles"], (list, tuple)):
        role = claims["roles"][0] if claims["roles"] else None
    return role

def require_role(*allowed_roles):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            role = _get_role()
            if role not in allowed_roles:
                return jsonify({"msg": "forbidden: requires role", "required": allowed_roles, "got": role}), 403
            return fn(*args, **kwargs)
        return wrapper
    return deco

def deny_roles(*denied_roles):
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            role = _get_role()
            if role in denied_roles:
                return jsonify({"msg": "forbidden for role", "role": role}), 403
            return fn(*args, **kwargs)
        return wrapper
    return deco
