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

@status_bp.get("/risk-summary")
def risk_summary():
    maintenance_count = _count(Maintenance)
    overdue_payments = db.session.query(Payment).filter(Payment.status == 'overdue').count()
    high_risk_tenants = 0  # Placeholder - could be calculated based on late payments
    
    total_alerts = maintenance_count + overdue_payments + high_risk_tenants
    
    return jsonify({
        "alerts": total_alerts,
        "breakdown": {
            "maintenance_issues": maintenance_count,
            "overdue_payments": overdue_payments,
            "high_risk_tenants": high_risk_tenants
        }
    })

@status_bp.get("/maintenance/hotspots/<int:property_id>")
def maintenance_hotspots(property_id):
    # Mock maintenance prediction data
    hotspots = [
        {
            "area": "HVAC System",
            "risk_score": 85,
            "predicted_issue": "Filter replacement needed",
            "estimated_date": "2024-02-15",
            "estimated_cost": 250
        },
        {
            "area": "Plumbing",
            "risk_score": 72,
            "predicted_issue": "Pipe maintenance",
            "estimated_date": "2024-03-01",
            "estimated_cost": 800
        },
        {
            "area": "Electrical",
            "risk_score": 45,
            "predicted_issue": "Minor repairs",
            "estimated_date": "2024-04-10",
            "estimated_cost": 350
        }
    ]
    
    return jsonify({
        "property_id": property_id,
        "hotspots": hotspots,
        "total_predicted_cost": sum(h["estimated_cost"] for h in hotspots),
        "high_risk_count": len([h for h in hotspots if h["risk_score"] >= 70])
    })

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
