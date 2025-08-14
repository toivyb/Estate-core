from flask import Blueprint, request, jsonify
from estatecore_backend import db
from estatecore_backend.models.incident_report import IncidentReport
from utils.auth import token_required
from datetime import datetime

incident = Blueprint('incident', __name__)

@incident.route('/api/report-incident', methods=['POST'])
@token_required
def report(current_user):
    data = request.json
    report = IncidentReport(
        user_id=current_user.id,
        property_id=data['property_id'],
        category=data['category'],
        description=data['description']
    )
    db.session.add(report)
    db.session.commit()
    return jsonify({"status": "received"})

@incident.route('/api/incidents/<int:property_id>', methods=['GET'])
@token_required
def list_incidents(current_user, property_id):
    reports = IncidentReport.query.filter_by(property_id=property_id).all()
    return jsonify([{
        "category": r.category,
        "description": r.description,
        "created_at": r.created_at.isoformat()
    } for r in reports])