from flask import Blueprint, request, jsonify
from utils.auth import token_required

geo = Blueprint('geo', __name__)

@geo.route('/api/unlock-by-location', methods=['POST'])
@token_required
def unlock_location(current_user):
    data = request.json
    if data.get("lat") and data.get("lng"):
        return jsonify({"unlocked": True})
    return jsonify({"unlocked": False}), 403