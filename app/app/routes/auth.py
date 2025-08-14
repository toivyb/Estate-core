from flask import Blueprint, request, jsonify
from estatecore_backend import db
from estatecore_backend.models.user import User
from datetime import datetime, timedelta
import jwt

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data.get('email')).first()
    if not user or not user.check_password(data.get('password', '')):
        return jsonify({'message': 'Invalid credentials'}), 401

    payload = {'user_id': user.id, 'exp': datetime.utcnow() + timedelta(hours=2)}
    token = jwt.encode(payload, 'your-secret-key', algorithm='HS256')
    return jsonify({'access_token': token})
