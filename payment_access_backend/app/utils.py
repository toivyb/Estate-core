"""
Utility functions and decorators for the payment‑based access control backend.
"""

from functools import wraps
from flask import request, jsonify

from .models import User


def require_role(role_name: str):
    """A decorator to restrict access to endpoints based on the user's role.

    The user's email is expected to be provided in the `X-User-Email` request
    header.  If the user is not found or does not match the required role,
    a 403 response is returned.
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            email = request.headers.get("X-User-Email")
            if not email:
                return jsonify(error="X-User-Email header missing"), 401
            user = User.query.filter_by(email=email).first()
            if not user or user.role != role_name:
                return jsonify(error="unauthorised"), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator