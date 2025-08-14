from flask import Blueprint, request, jsonify
from estatecore_backend.models.maintenance import MaintenanceRequest
from estatecore_backend.models import db
from datetime import datetime

maintenance_bp = Blueprint('maintenance', __name__)

@maintenance_bp.route('/api/maintenance', methods=['POST'])
def create_request():
    data = request.json
    m = MaintenanceRequest(
        property_id=data['property_id'],
        tenant_id=data.get('tenant_id'),
        description=data['description'],
        priority=data.get('priority', 'normal')
    )
    db.session.add(m)
    db.session.commit()
    return jsonify({"status": "success", "id": m.id})

@maintenance_bp.route('/api/maintenance', methods=['GET'])
def list_requests():
    prop = request.args.get('property_id')
    status = request.args.get('status')
    query = MaintenanceRequest.query
    if prop:
        query = query.filter_by(property_id=prop)
    if status:
        query = query.filter_by(status=status)
    requests = query.all()
    return jsonify(requests=[r.serialize() for r in requests])

@maintenance_bp.route('/api/maintenance/<int:req_id>', methods=['PATCH'])
def update_request(req_id):
    m = MaintenanceRequest.query.get(req_id)
    if not m:
        return jsonify({'error': 'Not found'}), 404
    data = request.json
    if 'status' in data: m.status = data['status']
    if 'assigned_to' in data: m.assigned_to = data['assigned_to']
    if 'priority' in data: m.priority = data['priority']
    m.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'status': 'success'})

@maintenance_bp.route('/api/maintenance/<int:req_id>', methods=['DELETE'])
def delete_request(req_id):
    m = MaintenanceRequest.query.get(req_id)
    if not m:
        return jsonify({'error': 'Not found'}), 404
    db.session.delete(m)
    db.session.commit()
    return jsonify({'status': 'deleted'})
