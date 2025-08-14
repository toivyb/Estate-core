from flask import Flask
from .extensions import init_extensions
from .routes.health import bp as health_bp

def create_app():
    app = Flask(__name__)
    # Load config via ENV VARS if provided; otherwise use lightweight defaults.
    app.config.from_prefixed_env()
    app.config.setdefault("SQLALCHEMY_DATABASE_URI", "sqlite:///estatecore.db")
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

    init_extensions(app)

    # Register minimal health endpoint
    app.register_blueprint(health_bp, url_prefix="/api")
    return app
