from estatecore_backend.extensions import db
# app/__init__.py
import os
from datetime import timedelta

from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_migrate import Migrate


jwt = JWTManager()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    # Core config
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev")
    app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "devjwt")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=12)

    db_url = os.environ.get("DATABASE_URL") or "postgresql://postgres:password@127.0.0.1:5433/estatecore_devestatecore.db"
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # CORS
    origins = [o.strip() for o in os.environ.get("CORS_ORIGINS", "*").split(",") if o.strip()]
    CORS(app, supports_credentials=True, origins=origins)

    # Init extensions
    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    # Blueprints
    from .routes.auth import bp as auth_bp
    from .routes.dashboard import bp as dash_bp
    from .routes.invites import bp as invites_bp
    from .routes.rent import bp as rent_bp
    from .routes.bulk import bp as bulk_bp
    from .routes.features import bp as features_bp

    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(dash_bp, url_prefix="/api")
    app.register_blueprint(invites_bp, url_prefix="/api")
    app.register_blueprint(rent_bp, url_prefix="/api")
    app.register_blueprint(bulk_bp, url_prefix="/api")
    app.register_blueprint(features_bp, url_prefix="/api")

    @app.get("/api/health")
    def health():
        return jsonify(ok=True)

    # Make sure models are imported so Alembic sees them
    with app.app_context():

    return app
