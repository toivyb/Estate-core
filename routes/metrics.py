from flask import Blueprint, jsonify

metrics_bp = Blueprint("metrics", __name__, url_prefix="/api/dashboard")

@metrics_bp.get("/metrics")
def metrics():
    return jsonify({
        "totals": {"tenants": 0, "users": 1, "properties": 0},
        "incomeVsCost": {"income": 0, "cost": 0, "net": 0},
    })
