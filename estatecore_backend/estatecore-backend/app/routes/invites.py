
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from .. import db
from ..models.invite import InviteToken
from ..models.user import User, Role
from ..models.property import Property, PropertyManager, Tenant

bp = Blueprint('invites', __name__)

@bp.post('/invites')
@jwt_required()
def create_invite():
    data = request.get_json() or {}
    email = data['email'].strip().lower()
    role_name = data['role_name']
    property_id = data['property_id']
    inv = InviteToken.generate(email, role_name, property_id)
    db.session.add(inv)
    db.session.commit()
    return jsonify({'token': inv.token, 'expires_at': inv.expires_at.isoformat()})

@bp.post('/invites/consume')
def consume_invite():
    data = request.get_json() or {}
    token = data['token']
    full_name = data['full_name']
    password = data['password']
    inv = InviteToken.query.filter_by(token=token).first()
    if not inv or inv.used_at:
        return {'msg':'invalid token'}, 400
    from datetime import datetime
    if inv.expires_at < datetime.utcnow():
        return {'msg':'token expired'}, 400

    # get/create user
    user = User.query.filter_by(email=inv.email).first()
    if not user:
        user = User(email=inv.email, full_name=full_name)
        user.set_password(password)
        db.session.add(user)

    # role
    role = Role.query.filter_by(name=inv.role_name).first()
    if not role:
        role = Role(name=inv.role_name)
        db.session.add(role)
        db.session.flush()
    if role not in user.roles:
        user.roles.append(role)

    # link to property
    prop = Property.query.get(inv.property_id)
    if inv.role_name in ('property_manager','property_admin'):
        pm = PropertyManager(user=user, property=prop, is_admin=(inv.role_name=='property_admin'))
        db.session.add(pm)
    elif inv.role_name == 'tenant':
        from ..models.property import Tenant as TenantModel
        t = TenantModel(user_id=user.id, property_id=prop.id)
        db.session.add(t)

    inv.used_at = datetime.utcnow()
    db.session.commit()
    return {'ok': True}
