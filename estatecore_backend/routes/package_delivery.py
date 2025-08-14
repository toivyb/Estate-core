from flask import Blueprint, request, jsonify
from estatecore_backend import db
from estatecore_backend.models.package_delivery import PackageDelivery
from estatecore_backend.utils.auth import token_required
from datetime import datetime

package_log = Blueprint('package_log', __name__)

@package_log.route('/api/packages', methods=['POST'])
@token_required
def log_package(current_user):
    data = request.json
    delivery = PackageDelivery(
        property_id=data['property_id'],
        tenant_id=data['tenant_id'],
        delivered_by=data['delivered_by'],
        status='Delivered'
    )
    db.session.add(delivery)
    db.session.commit()
    return jsonify({'message': 'Package logged'}), 201

@package_log.route('/api/packages/<int:property_id>', methods=['GET'])
@token_required
def get_packages(current_user, property_id):
    deliveries = PackageDelivery.query.filter_by(property_id=property_id).all()
    return jsonify([
        {
            'id': d.id,
            'tenant_id': d.tenant_id,
            'delivered_by': d.delivered_by,
            'picked_up_by': d.picked_up_by,
            'status': d.status,
            'created_at': d.created_at.isoformat(),
            'picked_up_at': d.picked_up_at.isoformat() if d.picked_up_at else None
        } for d in deliveries
    ])

@package_log.route('/api/packages/pickup/<int:package_id>', methods=['POST'])
@token_required
def mark_picked_up(current_user, package_id):
    delivery = PackageDelivery.query.get_or_404(package_id)
    delivery.status = 'Picked Up'
    delivery.picked_up_by = current_user.name
    delivery.picked_up_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'message': 'Package marked as picked up'})