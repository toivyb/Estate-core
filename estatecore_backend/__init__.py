from flask import Flask
from flask_cors import CORS
from .extensions import init_extensions
from .routes.health import bp as health_bp
from .routes.auth import auth_bp
from .routes.rent import rent_bp

def create_app():
    app = Flask(__name__)
    app.config.from_prefixed_env()
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///estatecore.db")
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    app.config.setdefault("SECRET_KEY", "change-me-in-prod")

    init_extensions(app)
    CORS(app)

    # Register blueprints
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(auth_bp)
    app.register_blueprint(rent_bp)

    return app
