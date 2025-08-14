from flask import Blueprint, request, jsonify
from utils.auth import token_required
import requests

gate_control = Blueprint('gate_control', __name__)

@token_required
@gate_control.route('/api/unlock-gate', methods=['POST'])
def unlock_gate(current_user):
    data = request.json
    gate_id = data['gate_id']
    property_id = data['property_id']

    # Check user permission (placeholder)
    if not current_user.has_access_to_gate(gate_id):
        return jsonify({'error': 'Access denied'}), 403

    # Call external trigger (e.g., webhook to controller)
    try:
        res = requests.post(f"http://controller.local/unlock/{gate_id}", timeout=2)
        if res.status_code == 200:
            return jsonify({'message': 'Gate unlocked'})
        else:
            return jsonify({'error': 'Controller error'}), 500
    except Exception:
        return jsonify({'error': 'Unable to reach gate controller'}), 500