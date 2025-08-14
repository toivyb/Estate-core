# app/routes/ai_routes.py

from flask import Blueprint, request, jsonify
from estatecore_backend.ai_models.predict.lease_scoring import score_lease
from estatecore_backend.ai_models.predict.rent_delay import predict_rent_delay
from estatecore_backend.ai_models.predict.maintenance_forecast import forecast_maintenance
from estatecore_backend.ai_models.predict.utility_forecast import forecast_utilities
from estatecore_backend.ai_models.predict.revenue_leakage import detect_revenue_leakage
from estatecore_backend.ai_models.predict.asset_health_score import get_asset_health_score
from estatecore_backend import db
from estatecore_backend.models.ai_summary import AISummary

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")

@ai_bp.route("/score-lease", methods=["POST"])
def api_score_lease():
    data = request.get_json() or {}
    return jsonify(score_lease(data))

@ai_bp.route("/predict-delay", methods=["POST"])
def api_predict_delay():
    data = request.get_json() or {}
    return jsonify(predict_rent_delay(data))

@ai_bp.route("/forecast-maintenance", methods=["POST"])
def api_forecast_maintenance():
    data = request.get_json() or {}
    return jsonify(forecast_maintenance(data))

@ai_bp.route("/forecast-utility", methods=["POST"])
def api_forecast_utility():
    data = request.get_json() or {}
    return jsonify(forecast_utilities(data))

@ai_bp.route("/detect-leakage", methods=["POST"])
def api_detect_leakage():
    data = request.get_json() or {}
    return jsonify(detect_revenue_leakage(data))

@ai_bp.route("/health-score", methods=["POST"])
def api_health_score():
    data = request.get_json() or {}
    return jsonify(get_asset_health_score(data))

@ai_bp.route("/save-summary", methods=["POST"])
def api_save_summary():
    data = request.get_json() or {}
    # Expect { "model_name": "...", "summary": "..." }
    record = AISummary(
        model_name=data.get("model_name", "unknown"),
        summary=data.get("summary", "")
    )
    db.session.add(record)
    db.session.commit()
    return jsonify({
        "message": "Saved",
        "id": record.id,
        "model_name": record.model_name,
        "created_at": record.created_at.isoformat()
    }), 201
