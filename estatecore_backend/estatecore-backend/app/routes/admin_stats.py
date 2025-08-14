from flask import Blueprint, jsonify
admin_stats_bp = Blueprint('admin_stats_bp', __name__)

@admin_stats_bp.route('/api/admin-stats', methods=['GET'])
def admin_stats():
    return jsonify({'rent_collected': 10000, 'expenses': 4000})
