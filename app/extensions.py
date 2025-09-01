from flask_sqlalchemy import SQLAlchemy

try:
    from flask_jwt_extended import JWTManager
    jwt = JWTManager()
except ImportError:
    jwt = None

db = SQLAlchemy()
