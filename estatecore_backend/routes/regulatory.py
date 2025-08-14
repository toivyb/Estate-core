from flask import Blueprint, jsonify
from estatecore_backend import db
from estatecore_backend.models.regulatory_doc import RegulatoryDoc
from utils.auth import token_required

regulatory = Blueprint('regulatory', __name__)

@regulatory.route('/api/regulatory-docs/<int:property_id>', methods=['GET'])
@token_required
def list_docs(current_user, property_id):
    records = RegulatoryDoc.query.filter_by(property_id=property_id).all()
    return jsonify([{
        "type": r.doc_type,
        "expires_on": r.expires_on.isoformat()
    } for r in records])