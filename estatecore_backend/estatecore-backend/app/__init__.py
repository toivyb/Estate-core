from estatecore_backend.extensions import db

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from .config_loader import load_config


migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)
    load_config(app)
    CORS(app)
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    from .models import register_models  # noqa
    register_models()

    from .routes import register_routes
    register_routes(app)

    return app
