from flask import Blueprint, request, jsonify
from estatecore_backend import db
from estatecore_backend.models.document import Document
from utils.auth import token_required
from datetime import datetime

vault = Blueprint('vault', __name__)

@vault.route('/api/documents', methods=['POST'])
@token_required
def upload_document(current_user):
    data = request.json
    doc = Document(
        property_id=data['property_id'],
        name=data['name'],
        type=data['type'],
        expires_on=datetime.strptime(data['expires_on'], "%Y-%m-%d")
    )
    db.session.add(doc)
    db.session.commit()
    return jsonify({"status": "uploaded"})

@vault.route('/api/documents/<int:property_id>', methods=['GET'])
@token_required
def list_documents(current_user, property_id):
    docs = Document.query.filter_by(property_id=property_id).all()
    return jsonify([{
        "name": d.name,
        "type": d.type,
        "expires_on": d.expires_on.isoformat()
    } for d in docs])