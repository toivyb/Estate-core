import jwt
from flask import g, request
from estatecore_backend.models import User

SECRET_KEY = 'your_secret_here'  # should match auth.py

@main.before_request
def load_user_from_token():
    auth = request.headers.get('Authorization')
    if not auth or not auth.startswith('Bearer '):
        g.current_user = None
        return
    token = auth.split()[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        g.current_user = User.query.get(payload['user_id'])
    except:
        g.current_user = None
