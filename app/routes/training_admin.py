
from flask import Blueprint, request, jsonify
from estatecore_backend import db
from estatecore_backend.models.training_log import TrainingLog

admin_train_bp = Blueprint("admin_train", __name__, url_prefix="/api/admin/train")

@admin_train_bp.route("/toggle", methods=["POST"])
def toggle_training():
    data = request.get_json()
    model = TrainingLog.query.filter_by(model_name=data["model"]).first()
    if not model:
        model = TrainingLog(model_name=data["model"])
    model.is_enabled = data["enabled"]
    db.session.add(model)
    db.session.commit()
    return jsonify({"message": f"{data['model']} training set to {data['enabled']}"})

@admin_train_bp.route("/status", methods=["GET"])
def get_status():
    logs = TrainingLog.query.all()
    return jsonify([
        {"model": log.model_name, "enabled": log.is_enabled, "last_trained": log.last_trained.isoformat() if log.last_trained else None}
        for log in logs
    ])
