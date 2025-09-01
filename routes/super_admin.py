from flask import Blueprint, jsonify, request
from utils.auth import token_required

admin_config = Blueprint('admin_config', __name__)
toggles = {"ai_enabled": True, "pdf_enabled": True}

@admin_config.route('/api/super-admin/toggles', methods=['GET', 'POST'])
@token_required
def toggle_features(current_user):
    global toggles
    if request.method == 'POST':
        toggles.update(request.json)
    return jsonify(toggles)