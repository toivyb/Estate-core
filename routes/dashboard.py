# estatecore_backend/routes/dashboard.py
from flask import Blueprint, jsonify
from .. import db
from ..models.maintenance import MaintenanceRequest

dashboard_bp = Blueprint("dashboard_bp", __name__, url_prefix="/api")


@dashboard_bp.get("/dashboard")
def get_dashboard():
    # Simple counts demo; expand as needed
    total = db.session.query(db.func.count(MaintenanceRequest.id)).scalar() or 0
    open_count = (
        db.session.query(db.func.count(MaintenanceRequest.id))
        .filter(MaintenanceRequest.status == "open")
        .scalar()
        or 0
    )
    closed_count = (
        db.session.query(db.func.count(MaintenanceRequest.id))
        .filter(MaintenanceRequest.status == "closed")
        .scalar()
        or 0
    )
    return jsonify(
        ok=True,
        maintenance={"total": total, "open": open_count, "closed": closed_count},
    ), 200
