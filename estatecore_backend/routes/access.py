from flask import Blueprint, request, jsonify
from estatecore_backend.models.access_log import AccessLog
from estatecore_backend.models.visitor_pass import VisitorPass, generate_pin
from estatecore_backend.models import db
from datetime import datetime

access_bp = Blueprint('access', __name__)

@access_bp.route('/api/access/log', methods=['POST'])
def log_access():
    data = request.json
    log = AccessLog(
        user_id=data['user_id'],
        door_id=data['door_id'],
        event_type=data['event_type'],
        reason=data.get('reason'),
        visitor_pass_id=data.get('visitor_pass_id')
    )
    db.session.add(log)
    db.session.commit()
    return jsonify({"status": "logged", "id": log.id})

@access_bp.route('/api/access/logs', methods=['GET'])
def get_logs():
    # Filters: user_id, date, event_type, door_id, visitor_pass_id
    query = AccessLog.query
    if 'user_id' in request.args:
        query = query.filter_by(user_id=request.args['user_id'])
    if 'event_type' in request.args:
        query = query.filter_by(event_type=request.args['event_type'])
    if 'door_id' in request.args:
        query = query.filter_by(door_id=request.args['door_id'])
    if 'visitor_pass_id' in request.args:
        query = query.filter_by(visitor_pass_id=request.args['visitor_pass_id'])
    logs = query.order_by(AccessLog.timestamp.desc()).all()
    return jsonify(logs=[l.serialize() for l in logs])

@access_bp.route('/api/visitor_pass', methods=['POST'])
def create_visitor_pass():
    data = request.json
    code = generate_pin()
    valid_from = datetime.strptime(data['valid_from'], '%Y-%m-%dT%H:%M')
    valid_until = datetime.strptime(data['valid_until'], '%Y-%m-%dT%H:%M')
    vp = VisitorPass(
        property_id=data['property_id'],
        issued_by_user_id=data['issued_by_user_id'],
        visitor_name=data['visitor_name'],
        code=code,
        valid_from=valid_from,
        valid_until=valid_until
    )
    db.session.add(vp)
    db.session.commit()
    return jsonify({"status": "created", "code": code, "id": vp.id})

@access_bp.route('/api/visitor_pass/use', methods=['POST'])
def use_visitor_pass():
    data = request.json
    now = datetime.utcnow()
    vp = VisitorPass.query.filter_by(code=data['code']).first()
    if not vp:
        return jsonify({"status": "invalid"}), 404
    if not (vp.valid_from <= now <= vp.valid_until):
        return jsonify({"status": "expired"}), 403
    if vp.used:
        return jsonify({"status": "already used"}), 403
    vp.used = True
    vp.used_at = now
    db.session.commit()
    # Log access
    log = AccessLog(
        user_id=data.get('user_id', 0),
        door_id=data['door_id'],
        event_type='visitor_entry',
        visitor_pass_id=vp.id,
        timestamp=now
    )
    db.session.add(log)
    db.session.commit()
    return jsonify({"status": "granted", "log_id": log.id})

# Mobile unlock endpoint (for integration with app)
@access_bp.route('/api/mobile/unlock', methods=['POST'])
def mobile_unlock():
    data = request.json
    # Validate user/gate/etc. logic here
    log = AccessLog(
        user_id=data['user_id'],
        door_id=data['door_id'],
        event_type='mobile_unlock',
        timestamp=datetime.utcnow()
    )
    db.session.add(log)
    db.session.commit()
    return jsonify({"status": "unlocked"})
