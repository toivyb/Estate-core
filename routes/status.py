# estatecore_backend/routes/status.py
from flask import Blueprint, jsonify
from sqlalchemy import func
from ..extensions import db
from ..models.tenant import Tenant
from ..models.lease import Lease
from ..models.payment import Payment
from ..models.expense import Expense
from ..models.utilitybill import UtilityBill
from ..models.message import Message
from ..models.application import Application
from ..models.maintenance import Maintenance
from ..models.feature_toggle import FeatureToggle

status_bp = Blueprint("status", __name__, url_prefix="/api/ai")

def _count(model):
    return db.session.query(func.count(model.id)).scalar() or 0

def _max_ts(model):
    try:
        return db.session.query(func.max(model.created_at)).scalar()
    except Exception:
        return None

def _feature_enabled(name: str, client_id: int = 1):
    row = FeatureToggle.query.filter_by(client_id=client_id, feature=name).first()
    return bool(row.enabled) if row else True  # default-on

@status_bp.get("/status")
def status():
    counts = {
        "tenants": _count(Tenant),
        "leases": _count(Lease),
        "payments": _count(Payment),
        "expenses": _count(Expense),
        "utility_bills": _count(UtilityBill),
        "messages": _count(Message),
        "applications": _count(Application),
        "maintenance": _count(Maintenance),
        "feature_toggles": _count(FeatureToggle),
    }
    updated = {
        "tenants": _max_ts(Tenant),
        "leases": _max_ts(Lease),
        "payments": _max_ts(Payment),
        "expenses": _max_ts(Expense),
        "utility_bills": _max_ts(UtilityBill),
        "messages": _max_ts(Message),
        "applications": _max_ts(Application),
        "maintenance": _max_ts(Maintenance),
        "feature_toggles": _max_ts(FeatureToggle),
    }
    features = {
        "lease_score": _feature_enabled("lease_score"),
        "rent_delay": _feature_enabled("rent_delay"),
        "expense_anomaly": _feature_enabled("expense_anomaly"),
        "cashflow": _feature_enabled("cashflow"),
        "asset_health": _feature_enabled("asset_health"),
        "revenue_leakage": _feature_enabled("revenue_leakage"),
        "sentiment": _feature_enabled("sentiment"),
        "maintenance_risk": _feature_enabled("maintenance_risk"),
    }
    # Simple readiness gates (tune as you like)
    ready = {
        "lease_score": counts["applications"] > 0 or (counts["tenants"] > 0 and counts["leases"] > 0),
        "rent_delay": counts["payments"] > 0,
        "expense_anomaly": counts["expenses"] >= 3,  # need some history
        "cashflow": counts["payments"] > 0 and counts["expenses"] > 0,
        "asset_health": counts["payments"] > 0 and counts["expenses"] > 0,
        "revenue_leakage": counts["leases"] > 0 and counts["payments"] > 0,
        "sentiment": counts["messages"] > 0,
        "maintenance_risk": counts["maintenance"] > 0 or counts["messages"] > 0,
    }
    return jsonify({
        "ok": True,
        "counts": counts,
        "last_updated": {k: (v.isoformat() if v else None) for k, v in updated.items()},
        "features_enabled": features,
        "features_ready": ready,
    })
