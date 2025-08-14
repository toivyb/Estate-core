from flask import Blueprint, jsonify
from utils.auth import token_required

analytics = Blueprint('analytics', __name__)

@analytics.route('/api/admin-stats', methods=['GET'])
@token_required
def stats(current_user):
    return jsonify({
        "rent_collected": 52000,
        "expenses": 17000,
        "active_tenants": 124
    })