# app/routes/refresh.py
"""Adds /api/refresh to the existing auth blueprint.
Ensure routes/__init__.py imports this module:
    from . import refresh  # noqa: F401
"""
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
# Use the existing /api auth blueprint
from .auth import bp  # type: ignore

@bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    ident = get_jwt_identity()
    new_access = create_access_token(identity=ident, fresh=False)
    return jsonify(access_token=new_access), 200
