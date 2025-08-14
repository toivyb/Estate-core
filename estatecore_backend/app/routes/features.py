from flask import Blueprint, jsonify, request
from ..models import FeatureFlag
from .. import db

bp = Blueprint("features", __name__)

@bp.get("/features")
def list_features():
    flags = FeatureFlag.query.all()
    return jsonify({f.key: f.enabled for f in flags})

@bp.post("/features/toggle")
def toggle_feature():
    data = request.get_json(force=True)
    key = data["key"]
    enabled = bool(data["enabled"])
    flag = FeatureFlag.query.filter_by(key=key).first()
    if not flag:
        flag = FeatureFlag(key=key, enabled=enabled)
        db.session.add(flag)
    else:
        flag.enabled = enabled
    db.session.commit()
    return jsonify({"key": key, "enabled": enabled})
