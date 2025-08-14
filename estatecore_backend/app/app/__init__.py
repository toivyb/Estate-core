from estatecore_backend.extensions import db
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from estatecore_backend.config import Config


migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    from estatecore_backend.routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    # Register your other blueprints here

    return app
