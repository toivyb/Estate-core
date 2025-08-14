from flask import Blueprint, jsonify
docs_bp = Blueprint('docs_bp', __name__)

@docs_bp.route('/api/regulatory-docs/<int:property_id>', methods=['GET'])
def regulatory_docs(property_id):
    # Dummy docs
    return jsonify([{'type': 'Lease', 'expires_on': '2025-12-31'}])
