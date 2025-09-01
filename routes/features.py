from flask import Blueprint, jsonify, request

features_bp = Blueprint("features", __name__, url_prefix="/api")

_FLAGS = {
    "ai_lease_scoring": True,
    "maintenance_prediction": True,
}

@features_bp.get("/feature-flags")
def list_flags():
    return jsonify([{"name": k, "enabled": v} for k, v in _FLAGS.items()])

@features_bp.patch("/feature-flags/<name>")
def toggle_flag(name):
    data = request.get_json() or {}
    enabled = bool(data.get("enabled"))
    _FLAGS[name] = enabled
    return jsonify({"name": name, "enabled": enabled})
