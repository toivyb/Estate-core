from flask import Blueprint, jsonify
from utils.auth import token_required

health_score = Blueprint('health_score', __name__)

@health_score.route('/api/asset-health/<int:property_id>', methods=['GET'])
@token_required
def get_asset_health(current_user, property_id):
    return jsonify({"property_id": property_id, "health_score": 84})