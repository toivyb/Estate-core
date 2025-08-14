from estatecore_backend.extensions import db
"""
Application factory for the payment‑based access control backend.

This module configures the Flask application, database, and migration
extensions.  It uses the factory pattern so that the app can be created
in different contexts (development, testing, etc.).
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from .config import Config

# Initialise extensions (instances are defined at module level but initialised
# in create_app)

migrate = Migrate()


def create_app() -> Flask:
    """Create and return a configured Flask application."""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialise database and migration extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints
    from .routes import main as main_bp
    app.register_blueprint(main_bp)

    return app