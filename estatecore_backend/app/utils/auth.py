

from functools import wraps
from flask import request, jsonify

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get("Authorization")
        if not token:
            return jsonify({"message": "Token is missing!"}), 403

        # Optional: Add real token verification logic here
        # e.g., decode JWT, check against DB, etc.

        return f(*args, **kwargs)
    return decorated
