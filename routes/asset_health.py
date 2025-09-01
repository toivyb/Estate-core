from flask import Blueprint, jsonify
from estatecore_backend.models.asset_health import AssetHealth
from utils.auth import token_required

health_score = Blueprint('health_score', __name__)

@health_score.route('/api/asset-health/<int:property_id>', methods=['GET'])
@token_required
def get_health(current_user, property_id):
    record = AssetHealth.query.filter_by(property_id=property_id).order_by(AssetHealth.generated_at.desc()).first()
    return jsonify({"score": record.score if record else None})