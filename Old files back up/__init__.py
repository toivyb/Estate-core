from flask import Flask
from .extensions import db, migrate  # Make sure extensions.py initializes these

def create_app():
    app = Flask(__name__)
    app.config.from_object("estatecore_backend.config.Config")

    db.init_app(app)
    migrate.init_app(app, db)

    # register blueprints here...

    return app
