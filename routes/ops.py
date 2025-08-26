from flask import Blueprint, jsonify
from ..models import db

ops_bp = Blueprint("ops", __name__)

@ops_bp.get("/")
def root_ok():
    # Fly smoke checks often hit "/"; respond 200 to avoid false failures
    return jsonify(status="ok")

@ops_bp.get("/healthz")
def healthz():
    return jsonify(status="ok")

@ops_bp.get("/readyz")
def readyz():
    try:
        db.session.execute(db.text("SELECT 1"))
        return jsonify(ready=True)
    except Exception as e:
        return jsonify(ready=False, error=str(e)), 500
