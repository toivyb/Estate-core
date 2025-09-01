from flask import Blueprint, jsonify, request
from .analytics import recompute_usage_stats, get_usage_summary
from .audit import log_event
from .folders import ensure_client_folder, ensure_building_folder, ensure_tenant_folder

bp = Blueprint("estatecore_audit", __name__, url_prefix="/api/audit")

@bp.route("/ensure-client-folders/<int:client_id>", methods=["POST"])
def api_ensure_client(client_id):
    path = ensure_client_folder(client_id)
    return jsonify({"ok": True, "path": path})

@bp.route("/ensure-building-folder/<int:client_id>/<int:building_id>", methods=["POST"])
def api_ensure_building(client_id, building_id):
    path = ensure_building_folder(client_id, building_id)
    return jsonify({"ok": True, "path": path})

@bp.route("/ensure-tenant-folder/<int:client_id>/<int:tenant_id>", methods=["POST"])
def api_ensure_tenant(client_id, tenant_id):
    path = ensure_tenant_folder(client_id, tenant_id)
    return jsonify({"ok": True, "path": path})

@bp.route("/log-feature", methods=["POST"])
def api_log_feature():
    data = request.get_json() or {}
    client_id = int(data.get("client_id"))
    feature = data.get("feature")
    log_event(client_id=client_id, entity_type="feature", action=feature, meta=data.get("meta"))
    return jsonify({"ok": True})

@bp.route("/recompute/<int:client_id>", methods=["POST"])
def api_recompute(client_id):
    recompute_usage_stats(client_id=client_id)
    s = get_usage_summary(client_id)
    return jsonify({"ok": True, "summary": {
        "top_features": s.top_features if s else [],
        "underused_features": s.underused_features if s else [],
    }})
