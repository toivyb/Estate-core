from flask import Blueprint, jsonify, request
super_admin_bp = Blueprint('super_admin_bp', __name__)

# In-memory toggles
TOGGLES = {'featureX': True, 'featureY': False}

@super_admin_bp.route('/api/super-admin/toggles', methods=['GET'])
def get_toggles():
    return jsonify(TOGGLES)

@super_admin_bp.route('/api/super-admin/toggles', methods=['POST'])
def set_toggles():
    updates = request.json
    TOGGLES.update(updates)
    return jsonify(TOGGLES)
