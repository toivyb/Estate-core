# app/routes/metrics.py
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from app.models import Tenant, Property, RentRecord  # ignore missing models gracefully

bp = Blueprint("metrics", __name__)

def _count(model):
    try:
        return model.query.count()
    except Exception:
        return 0

@bp.get("/dashboard/metrics")
@jwt_required()
def metrics():
    return jsonify({
        "tenants": _count(Tenant),
        "properties": _count(Property),
        "unpaid_rents": _count(RentRecord),  # adjust to filter by status if you have it
    }), 200
