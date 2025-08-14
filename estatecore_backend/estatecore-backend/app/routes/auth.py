
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from .. import db
from ..models.user import User, Role

bp = Blueprint('auth', __name__)

@bp.post('/login')
def login():
    data = request.get_json() or {}
    email = data.get('email','').strip().lower()
    password = data.get('password','')
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'msg':'bad credentials'}), 401
    roles = [r.name for r in user.roles]
    token = create_access_token(identity={'id': user.id, 'email': user.email, 'roles': roles})
    return jsonify({'access_token': token})

@bp.get('/me')
@jwt_required()
def me():
    ident = get_jwt_identity()
    return jsonify(ident)

@bp.post('/seed-admin')
def seed_admin():
    # simple unsafe seed; disable in prod
    email = request.json.get('email', 'admin@example.com')
    pwd = request.json.get('password', 'admin123')
    user = User.query.filter_by(email=email).first()
    if not user:
        user = User(email=email, full_name='Super Admin')
        user.set_password(pwd)
        db.session.add(user)
    # ensure super_admin role
    role = Role.query.filter_by(name='super_admin').first()
    if not role:
        role = Role(name='super_admin')
        db.session.add(role)
        db.session.flush()
    if role not in user.roles:
        user.roles.append(role)
    db.session.commit()
    return {'ok': True, 'email': email}
