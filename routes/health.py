from flask import Blueprint, jsonify
bp = Blueprint("health", __name__)

@bp.route("/api/healthz", methods=["GET"])
def healthz():
    return jsonify({"ok": True}), 200
